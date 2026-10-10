"""Unit tests for services/question_gen/budget.py."""
import pytest
from services.question_gen.budget import (
    calculate_total_questions,
    largest_remainder_allocation,
    build_question_budget,
)
import config


def test_calculate_total_questions():
    """Verify conversion of interview minutes to question counts."""
    assert calculate_total_questions(30, 3) == 10
    assert calculate_total_questions(45, 5) == 9
    assert calculate_total_questions(15, 3) == 5
    assert calculate_total_questions(2, 5) == 1  # Minimum 1 question
    assert calculate_total_questions(0, 3) == 1


def test_largest_remainder_allocation_guarantees_exact_sum():
    """Hare-Niemeyer rounding must guarantee the sum matches total_count."""
    items = [("A", 33.33), ("B", 33.33), ("C", 33.34)]
    for target in [1, 2, 5, 10, 17, 25]:
        alloc = largest_remainder_allocation(items, target)
        assert sum(alloc.values()) == target


def test_zero_weights_handling():
    """Items with all zero weights should be distributed as evenly as possible."""
    items = [("A", 0), ("B", 0), ("C", 0)]
    alloc = largest_remainder_allocation(items, 5)
    assert sum(alloc.values()) == 5
    assert set(alloc.values()).issubset({1, 2})


def test_single_skill_budget():
    """Single skill job must receive all allocated questions."""
    job = {
        "title": "Python Solo",
        "interview_duration": 30,
        "average_question_minutes": 5,
        "competencies": [
            {
                "name": "Programming",
                "weight": 100,
                "skills": [{"name": "Python", "weight": 100}]
            }
        ]
    }
    budget = build_question_budget(job)
    assert budget["total_questions"] == 6
    assert len(budget["allocation"]) == 1
    assert budget["allocation"][0]["skill"] == "Python"
    assert budget["allocation"][0]["total"] == 6
    assert sum(r["count"] for r in budget["rows"]) == 6


def test_multi_competency_budget_proportions():
    """Competency allocation follows weights with high fidelity."""
    job = {
        "title": "Backend Dev",
        "interview_duration": 30,
        "average_question_minutes": 3,  # 10 questions total
        "competencies": [
            {
                "name": "Backend",
                "weight": 60,
                "skills": [
                    {"name": "Python", "weight": 40},
                    {"name": "FastAPI", "weight": 20}
                ]
            },
            {
                "name": "Database",
                "weight": 40,
                "skills": [
                    {"name": "Postgres", "weight": 40}
                ]
            }
        ]
    }
    budget = build_question_budget(job)
    assert budget["total_questions"] == 10
    total_allocated = sum(item["total"] for item in budget["allocation"])
    assert total_allocated == 10
    total_row_count = sum(r["count"] for r in budget["rows"])
    assert total_row_count == 10


def test_short_interview_edge_case():
    """Very short interview duration should not crash and guarantee 1 question."""
    job = {
        "interview_duration": 3,
        "average_question_minutes": 5,
        "competencies": [
            {"name": "C1", "weight": 50, "skills": [{"name": "S1", "weight": 50}]},
            {"name": "C2", "weight": 50, "skills": [{"name": "S2", "weight": 50}]},
        ]
    }
    budget = build_question_budget(job)
    assert budget["total_questions"] == 1
    assert sum(item["total"] for item in budget["allocation"]) == 1


def test_small_plan_difficulty_distribution():
    """Verify that a 5-question plan with 20/50/30 intermediate distribution assigns easy, medium, and hard."""
    job = {
        "interview_duration": 25,
        "average_question_minutes": 5,  # 5 questions total
        "competencies": [
            {"name": "Backend", "weight": 50, "skills": [{"name": "Python", "weight": 30, "candidate_evidence": "strong"}, {"name": "FastAPI", "weight": 20, "candidate_evidence": "limited"}]},
            {"name": "Database", "weight": 30, "skills": [{"name": "Postgres", "weight": 30, "candidate_evidence": "strong"}]},
            {"name": "Architecture", "weight": 20, "skills": [{"name": "Design", "weight": 20, "candidate_evidence": "limited"}]},
        ]
    }
    budget = build_question_budget(job, candidate_band="intermediate")
    assert budget["total_questions"] == 5

    # Check difficulties across the entire plan
    total_easy = sum(alloc["easy"] for alloc in budget["allocation"])
    total_med = sum(alloc["medium"] for alloc in budget["allocation"])
    total_hard = sum(alloc["hard"] for alloc in budget["allocation"])

    assert total_easy == 1  # 20% of 5 = 1 easy!
    assert total_med == 3   # 50% of 5 = 2.5 -> 3 medium!
    assert total_hard == 1  # 30% of 5 = 1.5 -> 1 hard!
    assert total_easy + total_med + total_hard == 5
