from fastapi import APIRouter, HTTPException, status, Request
from typing import Dict, Any, List
from bson import ObjectId
import logging

from fastapi.responses import Response
from services.export import generate_plan_pdf

try:
    from db import get_database
except ImportError:
    from Backend.db import get_database

from models.schemas import InterviewPlan, PlanSettings
from services.assembly import assemble_interview_plan
from services.dedup import batch_embed_questions

router = APIRouter(prefix="/plans", tags=["Plans"])
logger = logging.getLogger("uvicorn")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_plan(payload: Dict[str, Any], request: Request):
    """
    POST /plans
    Orchestrates plan creation:
    1. Reads Job ID and Candidate ID from payload.
    2. Uses provided questions or generates them.
    3. Batch embeds questions for de-duplication.
    4. Assembles, ranks, and saves the plan to MongoDB.
    """
    db = get_database()
    
    job_id = payload.get("job_id")
    candidate_id = payload.get("candidate_id")
    raw_questions = payload.get("questions", [])
    competency_weights = payload.get("competency_weights", {})
    extracted_skills_map = payload.get("extracted_skills_map", {})
    
    if not job_id or not candidate_id:
        raise HTTPException(
            status_code=400,
            detail="Both 'job_id' and 'candidate_id' are required."
        )

    # Access pre-loaded embedding model from app_state
    embedding_model = getattr(request.app.state, "embedding_model", None)
    
    # 1. Compute embeddings for raw questions
    if raw_questions and embedding_model:
        raw_questions = batch_embed_questions(raw_questions, embedding_model)

    # 2. Assemble Plan
    settings = PlanSettings(**payload.get("settings", {}))
    plan_dict = assemble_interview_plan(
        job_id=job_id,
        candidate_id=candidate_id,
        raw_questions=raw_questions,
        competency_weights=competency_weights,
        extracted_skills_map=extracted_skills_map,
        settings=settings
    )

    # 3. Save to MongoDB 'interview_plans' collection
    result = await db["interview_plans"].insert_one(plan_dict)
    plan_id = str(result.inserted_id)
    
    # Format MongoDB _id for return
    plan_dict["_id"] = plan_id
    
    return {
        "message": "Interview plan created successfully.",
        "plan_id": plan_id,
        "plan": plan_dict
    }


@router.get("/{plan_id}", status_code=status.HTTP_200_OK)
async def get_plan(plan_id: str):
    """
    GET /plans/{plan_id}
    Retrieves an interview plan by ID.
    """
    db = get_database()
    
    if not ObjectId.is_valid(plan_id):
        raise HTTPException(status_code=400, detail="Invalid plan ID format.")

    plan = await db["interview_plans"].find_one({"_id": ObjectId(plan_id)})
    if not plan:
        raise HTTPException(status_code=404, detail="Interview plan not found.")

    plan["_id"] = str(plan["_id"])
    return plan


@router.get("/{plan_id}/export", status_code=status.HTTP_200_OK)
async def export_plan_pdf(plan_id: str):
    """
    GET /plans/{plan_id}/export
    Renders and downloads a clean PDF document for the specified interview plan.
    """
    db = get_database()
    
    if not ObjectId.is_valid(plan_id):
        raise HTTPException(status_code=400, detail="Invalid plan ID format.")

    plan = await db["interview_plans"].find_one({"_id": ObjectId(plan_id)})
    if not plan:
        raise HTTPException(status_code=404, detail="Interview plan not found.")

    # Generate PDF bytes
    pdf_bytes = generate_plan_pdf(
        plan_data=plan, 
        candidate_name="Sample Candidate", 
        job_title="Target Role"
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=interview_plan_{plan_id}.pdf"
        }
    )