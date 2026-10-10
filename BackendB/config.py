"""InterviewIQ - Backend B Configuration

Central configuration module loading environment variables and providing
typed application settings with sensible hackathon defaults.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dotenv import load_dotenv

# Base directory of the repository
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env.example")  # Fallback if .env is missing


def _env_str(name: str, default: str) -> str:
    return os.getenv(name, default)


def _env_float(name: str, default: float) -> float:
    val = os.getenv(name)
    if val is not None:
        try:
            return float(val)
        except ValueError:
            pass
    return default


def _env_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is not None:
        try:
            return int(val)
        except ValueError:
            pass
    return default


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is not None:
        return val.strip().lower() in ("1", "true", "yes", "on")
    return default


# ---- Gemini API Configuration --------------------------------------------
GEMINI_API_KEY = _env_str("GEMINI_API_KEY", "")
# Default to gemini-3.8-flash which is active, supported, and free-tier responsive
GEMINI_MODEL = _env_str("GEMINI_MODEL", "gemini-3.8-flash")
GEMINI_TEMPERATURE = _env_float("GEMINI_TEMPERATURE", 0.4)
GEMINI_TIMEOUT = _env_float("GEMINI_TIMEOUT", 45.0)
GEMINI_MAX_RETRIES = _env_int("GEMINI_MAX_RETRIES", 3)
RATE_LIMIT_BACKOFF_BASE = _env_float("RATE_LIMIT_BACKOFF_BASE", 6.0)
INCLUDE_LEVEL_EXAMPLES = _env_bool("INCLUDE_LEVEL_EXAMPLES", True)

# ---- Interview & Budget Defaults -----------------------------------------
AVERAGE_QUESTION_MINUTES = _env_float("AVERAGE_QUESTION_MINUTES", 3.0)
DEFAULT_INTERVIEW_MINUTES = _env_float("DEFAULT_INTERVIEW_MINUTES", 30.0)
MIN_COMPETENCY_SHARE = 0.10  # Competencies with >=10% weight get at least 1 question

# Generation Strategy: "single_call" (free-tier friendly) or "per_competency"
GENERATION_STRATEGY = _env_str("GENERATION_STRATEGY", "single_call")
MAX_CONCURRENT_LLM_CALLS = _env_int("MAX_CONCURRENT_LLM_CALLS", 1)

# ---- Difficulty Bands ----------------------------------------------------
DIFFICULTIES = ("easy", "medium", "hard")
DEFAULT_DIFFICULTY_MIX: Dict[str, Dict[str, int]] = {
    "beginner": {"easy": 50, "medium": 40, "hard": 10},
    "intermediate": {"easy": 20, "medium": 50, "hard": 30},
    "advanced": {"easy": 10, "medium": 30, "hard": 60},
}
DEFAULT_CANDIDATE_BAND = "intermediate"
SKILL_SHIFT_POINTS = 15  # Adjustment shift based on strong evidence or skill gap

# ---- Validation Limits ---------------------------------------------------
MIN_QUESTION_CHARS = 25
MAX_QUESTION_CHARS = 400
MIN_KEY_POINTS = 3
MAX_KEY_POINTS = 5
MAX_KEY_POINT_CHARS = 220
MAX_REGEN_ATTEMPTS = 3
MAX_REPLACEMENT_ROUNDS = 2

# ---- Caching & Data Paths ------------------------------------------------
CACHE_TTL_SECONDS = _env_int("CACHE_TTL_SECONDS", 3600)
DEMO_PLAN_PATH = BASE_DIR / "data" / "demo_plan.json"
MOCK_ANALYSIS_PATH = BASE_DIR / "data" / "mock_analysis.json"
SAMPLE_JOBS_PATH = BASE_DIR / "data" / "sample_jobs.json"
CACHE_DIR = BASE_DIR / "cache"


@dataclass
class GenerationSettings:
    """Per-request generation settings passed from API / caller."""
    interview_minutes: float = DEFAULT_INTERVIEW_MINUTES
    average_question_minutes: float = AVERAGE_QUESTION_MINUTES
    strategy: str = GENERATION_STRATEGY
    difficulty_override: Optional[Union[str, Dict[str, int]]] = None
    use_cache: bool = True
    max_concurrent_calls: int = MAX_CONCURRENT_LLM_CALLS
    demo_fallback: bool = True
