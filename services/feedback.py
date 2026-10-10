from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from db import get_database

logger = logging.getLogger("uvicorn")


async def log_feedback_action(
    plan_id: str,
    question_idx: int,
    question_text: str,
    action: str,  # "accept", "reject", "regenerate"
    hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Logs every accept, reject, or regenerate action with an optional hint 
    into the 'feedback' collection in MongoDB.
    """
    db = get_database()
    
    feedback_entry = {
        "plan_id": plan_id,
        "question_index": question_idx,
        "question_text": question_text,
        "action": action,
        "hint": hint,
        "timestamp": datetime.utcnow()
    }
    
    result = await db["feedback"].insert_one(feedback_entry)
    feedback_entry["_id"] = str(result.inserted_id)
    
    logger.info(f"Feedback logged: {action} on plan {plan_id}, question idx {question_idx}")
    return feedback_entry


async def get_candidate_question_history(candidate_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves all past questions associated with a candidate:
    1. Questions accepted/asked in previous interview plans.
    2. Questions previously rejected during review.
    
    Backend B uses this to populate the do-not-repeat/exclusion list.
    """
    db = get_database()
    history = []

    # 1. Fetch past plans for this candidate
    plans_cursor = db["interview_plans"].find({"candidate_id": candidate_id})
    past_plans = await plans_cursor.to_list(length=100)

    for plan in past_plans:
        questions = plan.get("questions", [])
        for q in questions:
            if q.get("status") in ["accepted", "pending"]:
                history.append({
                    "question": q.get("question"),
                    "embedding": q.get("embedding"),
                    "source": "past_plan"
                })

    # 2. Fetch rejected questions from feedback logs
    feedback_cursor = db["feedback"].find({"action": "reject"})
    rejected_logs = await feedback_cursor.to_list(length=100)

    for log in rejected_logs:
        if log.get("question_text"):
            history.append({
                "question": log.get("question_text"),
                "source": "rejected_feedback"
            })

    return history