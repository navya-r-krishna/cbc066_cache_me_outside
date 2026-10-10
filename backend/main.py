
import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pymongo.errors import PyMongoError

try:
    from .config import settings
    from .database import (
        candidates_collection,
        jobs_collection,
        check_database_connection,
    )
    from .services.candidate_profile import (
        build_candidate_profile,
        compare_candidate_to_job,
    )
    from .services.skill_analysis import analyze_job
except ImportError:
    from config import settings
    from database import (
        candidates_collection,
        jobs_collection,
        check_database_connection,
    )
    from services.candidate_profile import (
        build_candidate_profile,
        compare_candidate_to_job,
    )
    from services.skill_analysis import analyze_job


logger = logging.getLogger(__name__)

app = FastAPI(
    title="InterviewIQ API",
    description="Resume analysis and interview preparation backend",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CandidateAnalysisRequest(BaseModel):
    role_title: str = Field(..., min_length=1)
    job_description: str = Field(..., min_length=1)
    resume_text: str | None = None
    resume_pdf_path: str | None = None


class CreateJobRequest(BaseModel):
    role_title: str = Field(..., min_length=1, max_length=200)
    job_description: str = Field(..., min_length=1)


class CreateCandidateRequest(BaseModel):
    candidate_name: str | None = Field(default=None, max_length=200)
    resume_text: str | None = None
    resume_pdf_path: str | None = None


class SkillWeightUpdate(BaseModel):
    name: str = Field(..., min_length=1)
    weight: float = Field(..., gt=0)


class UpdateJobSkillsRequest(BaseModel):
    skills: list[SkillWeightUpdate] = Field(..., min_length=1)


def serialize_document(document: dict[str, Any]) -> dict[str, Any]:
    """Convert MongoDB values into JSON-friendly values."""
    result = dict(document)
    result["id"] = str(result.pop("_id"))
    for key, value in result.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
    return result


def normalize_weights(skills: list[dict[str, Any]]) -> None:
    total = sum(float(skill["weight"]) for skill in skills)
    if total <= 0:
        raise ValueError("The total skill weight must be greater than zero.")

    for skill in skills:
        skill["normalized_weight"] = round(
            float(skill["weight"]) / total, 6
        )

    # Correct rounding drift so the displayed values sum to 1.
    if skills:
        drift = round(
            1.0 - sum(skill["normalized_weight"] for skill in skills), 6
        )
        skills[-1]["normalized_weight"] = round(
            skills[-1]["normalized_weight"] + drift, 6
        )


@app.get("/")
def root() -> dict[str, Any]:
    return {"success": True, "message": "InterviewIQ API is running"}


@app.get("/health")
def health_check() -> dict[str, Any]:
    return {
        "status": "healthy",
        "database": "connected" if check_database_connection() else "unavailable",
    }


@app.post("/api/analysis/candidate")
def analyze_candidate(request: CandidateAnalysisRequest) -> dict[str, Any]:
    """Compare a candidate resume against a job description."""
    if bool(request.resume_text) == bool(request.resume_pdf_path):
        raise HTTPException(
            status_code=400,
            detail="Provide exactly one of resume_text or resume_pdf_path.",
        )

    try:
        candidate = build_candidate_profile(
            resume_text=request.resume_text,
            resume_pdf_path=request.resume_pdf_path,
        )
        job = analyze_job(
            request.job_description,
            role_title=request.role_title,
        )
        comparison = compare_candidate_to_job(
            candidate,
            job,
            job_description=request.job_description,
        )

        return {
            "success": True,
            "message": "Candidate analysis completed",
            "data": {
                "candidate_profile": candidate,
                "job_analysis": job,
                "comparison": comparison,
            },
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="The specified resume PDF was not found.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("Candidate analysis failed")
        raise HTTPException(
            status_code=500,
            detail="Candidate analysis failed. Check backend logs.",
        )


@app.post("/api/jobs", status_code=201)
def create_job(request: CreateJobRequest) -> dict[str, Any]:
    """Analyze a job description and save the analysis to MongoDB."""
    try:
        analysis = analyze_job(
            request.job_description,
            role_title=request.role_title,
        )

        document = {
            "role_title": request.role_title.strip(),
            "job_description": request.job_description.strip(),
            "analysis": analysis,
            "weighted_skills": analysis.get("weighted_skills", []),
            "low_info": analysis.get("low_info", False),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        result = jobs_collection.insert_one(document)
        saved = jobs_collection.find_one({"_id": result.inserted_id})

        return {
            "success": True,
            "message": "Job analyzed and saved",
            "data": serialize_document(saved),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except PyMongoError:
        logger.exception("Could not save job")
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Check MongoDB Atlas configuration.",
        )


@app.patch("/api/jobs/{job_id}/skills")
def update_job_skills(
    job_id: str,
    request: UpdateJobSkillsRequest,
) -> dict[str, Any]:
    """Update job skill weights and recompute normalized weights."""
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID.")

    try:
        job = jobs_collection.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")

        current_skills = job.get("weighted_skills", [])
        skills_by_name = {
            skill["name"].casefold(): dict(skill)
            for skill in current_skills
        }

        submitted_names = [item.name.strip().casefold() for item in request.skills]
        if len(submitted_names) != len(set(submitted_names)):
            raise HTTPException(
                status_code=400,
                detail="Each skill can be updated only once per request.",
            )

        for item in request.skills:
            key = item.name.strip().casefold()
            if key not in skills_by_name:
                raise HTTPException(
                    status_code=400,
                    detail=f"Skill '{item.name}' was not found in this job analysis.",
                )
            skills_by_name[key]["weight"] = item.weight

        updated_skills = list(skills_by_name.values())
        normalize_weights(updated_skills)

        analysis = dict(job.get("analysis", {}))
        analysis["weighted_skills"] = updated_skills
        analysis["summary"] = dict(analysis.get("summary", {}))
        analysis["summary"]["normalized_weight_sum"] = round(
            sum(skill["normalized_weight"] for skill in updated_skills), 6
        )

        jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "weighted_skills": updated_skills,
                    "analysis": analysis,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

        saved = jobs_collection.find_one({"_id": ObjectId(job_id)})
        return {
            "success": True,
            "message": "Job skill weights updated",
            "data": serialize_document(saved),
        }
    except HTTPException:
        raise
    except PyMongoError:
        logger.exception("Could not update job skills")
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Check MongoDB Atlas configuration.",
        )


@app.post("/api/candidates", status_code=201)
def create_candidate(request: CreateCandidateRequest) -> dict[str, Any]:
    """Parse a resume and save the resulting candidate profile."""
    if bool(request.resume_text) == bool(request.resume_pdf_path):
        raise HTTPException(
            status_code=400,
            detail="Provide exactly one of resume_text or resume_pdf_path.",
        )

    try:
        profile = build_candidate_profile(
            resume_text=request.resume_text,
            resume_pdf_path=request.resume_pdf_path,
        )

        document = {
            "candidate_name": (
                request.candidate_name.strip()
                if request.candidate_name
                else None
            ),
            "profile": profile,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        result = candidates_collection.insert_one(document)
        saved = candidates_collection.find_one({"_id": result.inserted_id})

        return {
            "success": True,
            "message": "Candidate profile created",
            "data": serialize_document(saved),
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="The specified resume PDF was not found.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except PyMongoError:
        logger.exception("Could not save candidate")
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Check MongoDB Atlas configuration.",
        )
    except Exception:
        logger.exception("Candidate profile creation failed")
        raise HTTPException(
            status_code=500,
            detail="Candidate profile creation failed. Check backend logs.",
        )
