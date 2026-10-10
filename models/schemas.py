from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

# --- ENUMS ---
class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class QuestionStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class CandidateBand(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

# --- SUB-MODELS ---
class ExtractedSkill(BaseModel):
    skill: str
    weight: float = Field(..., ge=0.0, le=1.0, description="Normalized skill weight (0-1)")
    level: str = Field(..., description="required or preferred")
    evidence: str = Field(..., description="Reasoning for weight allocation")

class CompetencyGroup(BaseModel):
    competency: str
    skills: List[str]
    total_weight: float

class QuestionItem(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    competency: str
    skill: str
    difficulty: DifficultyLevel
    question: str
    rationale: str
    key_points: List[str]
    status: QuestionStatus = QuestionStatus.PENDING
    embedding: Optional[List[float]] = None
    response: Optional[str] = None
    score: Optional[float] = None
    feedback_notes: Optional[str] = None

# --- MAIN DATABASE MODELS ---
class JobDescription(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    raw_text: str
    title: Optional[str] = "Target Role"
    skills: List[ExtractedSkill]
    competency_groups: List[CompetencyGroup]
    low_info: bool = False
    experience_level_asked: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CandidateProfile(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    raw_resume_markdown: str
    extracted_skills: List[str]
    experience_years: float
    education: List[str]
    score: float = Field(..., ge=0.0, le=100.0)
    band: CandidateBand
    gaps: List[str] = Field(default_factory=list, description="Missing JD skills")
    strengths: List[str] = Field(default_factory=list)
    past_questions_history: List[Dict[str, Any]] = Field(default_factory=list)

class PlanSettings(BaseModel):
    interview_length_minutes: int = 45
    avg_minutes_per_question: float = 3.0
    overall_difficulty_override: Optional[DifficultyLevel] = None

class InterviewPlan(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    job_id: str
    candidate_id: str
    settings: PlanSettings
    questions: List[QuestionItem]
    coverage_summary: Dict[str, float] = Field(default_factory=dict)
    status: str = "created"  # created, in_review, finalized
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FeedbackLog(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    plan_id: str
    question_id: str
    action: str  # accept, reject, regenerate
    hint: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow) 