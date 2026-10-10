from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExperienceLevel(str, Enum):
    INTERN = "intern"
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    STAFF = "staff"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionCategory(str, Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system_design"
    CODING = "coding"
    PROBLEM_SOLVING = "problem_solving"


class QuestionModel(BaseModel):
    id: str = Field(..., description="Unique question identifier")
    category: QuestionCategory = Field(default=QuestionCategory.TECHNICAL)
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.MEDIUM)
    question: str = Field(..., description="Interview question text")
    context: Optional[str] = Field(None, description="Optional background scenario or context")
    expected_key_points: List[str] = Field(default_factory=list, description="Key concepts candidate should mention")
    suggested_answer: Optional[str] = Field(None, description="Model reference answer")
    hints: List[str] = Field(default_factory=list, description="Helpful hints for the candidate")


class GenerateInterviewRequest(BaseModel):
    role: str = Field(..., description="Target job title (e.g. Fullstack Engineer, Data Scientist)")
    experience_level: ExperienceLevel = Field(default=ExperienceLevel.MID)
    tech_stack: List[str] = Field(default_factory=list, description="Technologies/languages/frameworks")
    job_description: Optional[str] = Field(None, description="Optional job description text")
    resume_text: Optional[str] = Field(None, description="Optional extracted resume text")
    num_questions: int = Field(default=5, ge=1, le=20, description="Total number of questions to generate")
    categories: List[QuestionCategory] = Field(
        default_factory=lambda: [QuestionCategory.TECHNICAL, QuestionCategory.BEHAVIORAL],
        description="Types of questions desired"
    )
    custom_instructions: Optional[str] = Field(None, description="Additional prompt guidelines")


class AnswerSubmission(BaseModel):
    session_id: str
    question_id: str
    candidate_answer: str


class EvaluationResult(BaseModel):
    question_id: str
    score: float = Field(..., ge=0.0, le=10.0, description="Score out of 10")
    feedback: str = Field(..., description="Constructive evaluation feedback")
    strengths: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)
    key_points_covered: List[str] = Field(default_factory=list)
    missing_key_points: List[str] = Field(default_factory=list)


class InterviewSessionModel(BaseModel):
    session_id: str
    role: str
    experience_level: ExperienceLevel
    tech_stack: List[str] = Field(default_factory=list)
    questions: List[QuestionModel] = Field(default_factory=list)
    evaluations: Dict[str, EvaluationResult] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="active", description="active, completed, archived")
    overall_score: Optional[float] = None
    overall_summary: Optional[str] = None


class ApiResponse(BaseModel):
    success: bool = True
    message: str = "Operation successful"
    data: Optional[Any] = None
