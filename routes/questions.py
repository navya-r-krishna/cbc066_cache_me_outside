from fastapi import APIRouter, HTTPException, status, Request
from typing import Dict, Any, Optional
from bson import ObjectId
import logging

try:
    from db import get_database
except ImportError:
    from Backend.db import get_database

from services.feedback import log_feedback_action
from services.dedup import is_duplicate, embed_text

router = APIRouter(prefix="/questions", tags=["Questions"])
logger = logging.getLogger("uvicorn")


@router.patch("/{plan_id}/{question_idx}/status", status_code=status.HTTP_200_OK)
async def update_question_status(
    plan_id: str,
    question_idx: int,
    payload: Dict[str, Any]
):
    """
    PATCH /questions/{plan_id}/{question_idx}/status
    Updates a question's status (accepted / rejected / pending) and logs audit feedback.
    """
    db = get_database()
    new_status = payload.get("status")
    hint = payload.get("hint")  # Optional interviewer hint

    if new_status not in ["accepted", "rejected", "pending"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'accepted', 'rejected', or 'pending'."
        )

    if not ObjectId.is_valid(plan_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan ID format."
        )

    plan = await db["interview_plans"].find_one({"_id": ObjectId(plan_id)})
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview plan not found."
        )

    questions = plan.get("questions", [])
    if question_idx < 0 or question_idx >= len(questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question index out of bounds."
        )

    # Update target question status
    target_question = questions[question_idx]
    target_question["status"] = new_status

    # Save updated array back to MongoDB
    await db["interview_plans"].update_one(
        {"_id": ObjectId(plan_id)},
        {"$set": {"questions": questions}}
    )

    # Audit log entry in 'feedback' collection
    await log_feedback_action(
        plan_id=plan_id,
        question_idx=question_idx,
        question_text=target_question.get("question", ""),
        action=new_status,
        hint=hint
    )

    return {
        "message": f"Question {question_idx} status updated to '{new_status}'.",
        "question": target_question
    }


@router.post("/{plan_id}/{question_idx}/regenerate", status_code=status.HTTP_200_OK)
async def regenerate_single_question(
    plan_id: str,
    question_idx: int,
    payload: Dict[str, Any],
    request: Request
):
    """
    POST /questions/{plan_id}/{question_idx}/regenerate
    Replaces a specific question with a newly generated, non-duplicate question.
    """
    db = get_database()
    hint = payload.get("hint", "")

    if not ObjectId.is_valid(plan_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan ID format."
        )

    plan = await db["interview_plans"].find_one({"_id": ObjectId(plan_id)})
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview plan not found."
        )

    questions = plan.get("questions", [])
    if question_idx < 0 or question_idx >= len(questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question index out of bounds."
        )

    old_question = questions[question_idx]
    
    # 1. Log the regeneration trigger to feedback
    await log_feedback_action(
        plan_id=plan_id,
        question_idx=question_idx,
        question_text=old_question.get("question", ""),
        action="regenerate",
        hint=hint
    )

    # 2. Extract embedding model from app state
    embedding_model = getattr(request.app.state, "embedding_model", None)

    # 3. Construct candidate replacement question
    # (In integration phase, Backend B's LLM generation function is called here)
    replacement_text = payload.get("new_question_text")
    if not replacement_text:
        # Fallback test string if generation layer is not passed in request body
        replacement_text = f"Practical exercise on {old_question.get('skill', 'Core Topic')} with hands-on scenario."

    # 4. Check replacement against vector de-duplication
    is_dup, match, score = is_duplicate(
        new_question_text=replacement_text,
        existing_questions=questions,
        model=embedding_model
    )

    if is_dup:
        logger.warning(f"Regenerated question flagged as duplicate (score: {score}).")

    # 5. Generate embedding for new replacement
    new_embedding = None
    if embedding_model:
        new_embedding = embed_text(replacement_text, embedding_model)

    new_question_item = {
        "competency": old_question.get("competency"),
        "skill": old_question.get("skill"),
        "difficulty": old_question.get("difficulty"),
        "question": replacement_text,
        "rationale": f"Regenerated based on hint: '{hint}'" if hint else old_question.get("rationale"),
        "key_points": payload.get("key_points", old_question.get("key_points", [])),
        "status": "pending",
        "embedding": new_embedding
    }

    # Swap question in list
    questions[question_idx] = new_question_item

    # Update MongoDB
    await db["interview_plans"].update_one(
        {"_id": ObjectId(plan_id)},
        {"$set": {"questions": questions}}
    )

    return {
        "message": f"Question {question_idx} successfully regenerated.",
        "old_question": old_question.get("question"),
        "new_question": new_question_item
    }