"""Unit tests for services/regenerate/regenerate_service.py."""
import pytest
from llm.client import GeminiClient
from llm.prompts import SingleQuestionResponse
from services.regenerate.regenerate_service import regenerate_question


def make_single_transport(question_text="How would you design a rate limiter in Python?"):
    def _transport(prompt, schema):
        return SingleQuestionResponse(
            skill="Python",
            difficulty="medium",
            question=question_text,
            key_points=["Token bucket algorithm", "Redis atomic counter", "HTTP 429 status code"]
        )
    return _transport


@pytest.mark.asyncio
async def test_regenerate_question_success():
    """Regeneration returns new question matching skill and difficulty with feedback logged."""
    original = {
        "id": "q_001",
        "competency": "Backend Development",
        "skill": "Python",
        "difficulty": "medium",
        "question": "What are Python decorators and how are they used?",
        "key_points": ["Higher-order functions", "functools.wraps"]
    }
    plan = {
        "job_title": "Python Developer",
        "questions": [original]
    }

    feedback_records = []
    client = GeminiClient(transport=make_single_transport("How would you implement a custom context manager in Python using generators?"))

    new_q = await regenerate_question(
        question=original,
        plan=plan,
        hint="more practical",
        client=client,
        feedback_logger=feedback_records.append,
    )

    assert new_q["id"] != original["id"]
    assert new_q["skill"] == original["skill"]
    assert new_q["difficulty"] == original["difficulty"]
    assert new_q["question"] != original["question"]
    assert new_q["text"] == new_q["question"]
    assert len(feedback_records) == 1
    assert feedback_records[0]["action"] in ("regenerate", "regenerated")
    assert feedback_records[0]["hint"] == "more practical"


@pytest.mark.asyncio
async def test_regenerate_avoids_duplicates():
    """Regeneration retries if returned question matches exclusion list."""
    attempt = {"count": 0}
    original_text = "How would you optimize a slow database query in Postgres?"

    def transport(prompt, schema):
        attempt["count"] += 1
        if attempt["count"] == 1:
            # Returns question identical to existing question in plan
            return SingleQuestionResponse(
                skill="SQL",
                difficulty="medium",
                question=original_text,
                key_points=["Explain plan", "Add index"]
            )
        else:
            # Returns new distinct question
            return SingleQuestionResponse(
                skill="SQL",
                difficulty="medium",
                question="How do partial indexes improve query performance for sparse status columns?",
                key_points=["WHERE clause indexing", "Index size reduction", "Write overhead savings"]
            )

    original = {
        "id": "q_002",
        "competency": "Database",
        "skill": "SQL",
        "difficulty": "medium",
        "question": original_text,
        "key_points": ["Explain plan"]
    }
    plan = {"job_title": "Data Engineer", "questions": [original]}
    client = GeminiClient(transport=transport)

    new_q = await regenerate_question(question=original, plan=plan, client=client)
    assert attempt["count"] == 2
    assert new_q["question"] != original_text

