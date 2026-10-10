"""Unit tests for llm/prompts.py prompt construction and engineering rules."""
import pytest
import config
from llm.prompts import (
    PROMPT_VERSION,
    LEVEL_CALIBRATION_EXAMPLES,
    build_question_generation_prompt,
    build_regeneration_prompt,
)


def test_generation_prompt_contains_rules_and_time_budgets():
    """Verify build_question_generation_prompt contains the 'ONE thing only' rule and time budgets."""
    slots = [{"competency": "Backend", "skill": "Python", "difficulty": "medium", "count": 1}]
    prompt = build_question_generation_prompt(
        job_title="Python Engineer",
        job_summary="Backend REST services",
        requested_slots=slots,
        candidate_band="intermediate",
        candidate_strengths=["Python"],
        candidate_gaps=["Kafka"],
    )

    # 1. Rule: Ask ONE thing only
    assert "ONE thing only" in prompt
    assert 'Do not join two separate tasks with "and"' in prompt

    # 2. Time budgets
    assert "1-2 minutes" in prompt
    assert "3-4 minutes" in prompt
    assert "6-8 minutes" in prompt

    # 3. Stay inside listed skill rule
    assert "Stay inside the listed skill" in prompt

    # 4. Calibration examples included by default
    assert "CALIBRATION EXAMPLES (for calibration only, never reuse):" in prompt
    for ex in LEVEL_CALIBRATION_EXAMPLES.values():
        assert ex in prompt


def test_regeneration_prompt_contains_more_practical_rule():
    """Verify build_regeneration_prompt contains the 'more practical' rule."""
    prompt = build_regeneration_prompt(
        job_title="Python Engineer",
        competency="Backend",
        skill="Python",
        difficulty="medium",
        original_question="How do you handle memory management in Python?",
        hint="more practical",
    )

    # 1. Rule: ONE thing only
    assert "ONE thing only" in prompt
    assert 'Do not join two separate tasks with "and"' in prompt

    # 2. Rule: more practical
    assert "more practical" in prompt
    assert "Do NOT make the question longer or harder" in prompt


def test_prompt_version_constant_is_set():
    """PROMPT_VERSION constant is defined for cache invalidation."""
    assert PROMPT_VERSION == "2"
