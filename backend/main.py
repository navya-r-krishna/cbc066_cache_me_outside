import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pymongo.errors import PyMongoError
from sentence_transformers import SentenceTransformer

import os
import sys

# Ensure root project directory is first in sys.path so root packages resolve cleanly
_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.abspath(os.path.join(_current_dir, ".."))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)
if _current_dir not in sys.path:
    sys.path.append(_current_dir)

# System & Local DB imports
try:
    from Backend.db import connect_to_mongo, close_mongo_connection
    from Backend.config import settings
    from Backend.database import (
        candidates_collection,
        jobs_collection,
        check_database_connection,
    )
    from Backend.services.candidate_profile import (
        build_candidate_profile,
        compare_candidate_to_job,
    )
    from Backend.services.skill_analysis import analyze_job
except ImportError:
    from .db import connect_to_mongo, close_mongo_connection
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

from routes.plans import router as plans_router
from routes.questions import router as questions_router



logger = logging.getLogger("uvicorn")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events cleanly:
    1. Connects to MongoDB Atlas instance.
    2. Pre-loads the SentenceTransformer embedding model into app state.
    3. Closes MongoDB connections on shutdown.
    """
    logger.info("Starting up application...")
    await connect_to_mongo()

    # Pre-load embedding model for Backend C vector deduplication
    try:
        logger.info("Loading embedding model: all-MiniLM-L6-v2...")
        app.state.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Embedding model loaded successfully!")
    except Exception as e:
        logger.warning(f"Could not load SentenceTransformer model: {e}")
        app.state.embedding_model = None

    yield

    logger.info("Shutting down application...")
    await close_mongo_connection()


app = FastAPI(
    title="InterviewIQ API",
    description="Unified API combining Resume/JD Analysis and Interview Plan Generation",
    version="1.2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "CORS_ORIGINS", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Backend C Routers
app.include_router(plans_router)
app.include_router(questions_router)


# --- Backend A Schemas ---

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


# --- Helper Functions ---

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


# --- Core System Endpoints ---

@app.get("/")
def root() -> dict[str, Any]:
    return {"success": True, "message": "InterviewIQ Unified API is running"}


@app.get("/health")
def health_check() -> dict[str, Any]:
    return {
        "status": "healthy",
        "database": "connected" if check_database_connection() else "unavailable",
    }


# --- Backend A Endpoints ---

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


@app.post("/api/jobs", status_code=status.HTTP_201_CREATED)
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
    """Update skill weights and synchronize competency groups."""
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

        submitted_names = [
            item.name.strip().casefold()
            for item in request.skills
        ]
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

        updated_by_name = {
            skill["name"].casefold(): skill
            for skill in updated_skills
        }

        analysis = dict(job.get("analysis", {}))
        analysis["weighted_skills"] = updated_skills

        refreshed_groups = []
        for original_group in analysis.get("competency_groups", []):
            group = dict(original_group)
            refreshed_skills = []

            for original_skill in original_group.get("skills", []):
                key = original_skill["name"].casefold()
                updated_skill = updated_by_name.get(key)

                if updated_skill is not None:
                    refreshed_skills.append(dict(updated_skill))
                else:
                    refreshed_skills.append(dict(original_skill))

            group["skills"] = refreshed_skills
            group["skill_count"] = len(refreshed_skills)
            group["total_weight"] = round(
                sum(skill["weight"] for skill in refreshed_skills), 6
            )
            group["total_normalized_weight"] = round(
                sum(
                    skill["normalized_weight"]
                    for skill in refreshed_skills
                ),
                6,
            )
            refreshed_groups.append(group)

        analysis["competency_groups"] = refreshed_groups

        analysis["summary"] = dict(analysis.get("summary", {}))
        analysis["summary"]["normalized_weight_sum"] = round(
            sum(
                skill["normalized_weight"]
                for skill in updated_skills
            ),
            6,
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


@app.post("/api/candidates", status_code=status.HTTP_201_CREATED)
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)