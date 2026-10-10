"""Regression tests for the skill-matching and slot bugs."""
from collections import Counter
from utils.validators import validate_question_batch


def _q(skill, diff="easy"):
    return {"skill": skill, "difficulty": diff,
            "question": "Explain how you would approach this problem in a real project.",
            "key_points": ["first point", "second point"]}


def test_nosql_does_not_fill_a_sql_slot():
    slots = Counter({("Databases", "SQL", "easy"): 1})
    r = validate_question_batch([_q("NoSQL")], open_slots=slots)
    assert r.valid == []
    assert slots[("Databases", "SQL", "easy")] == 1


def test_java_does_not_fill_a_javascript_slot():
    slots = Counter({("Web", "JavaScript", "easy"): 1})
    assert validate_question_batch([_q("Java")], open_slots=slots).valid == []


def test_skill_name_is_canonicalised_to_the_budget_slot():
    slots = Counter({("Backend", "Python", "easy"): 1})
    r = validate_question_batch([_q("Python 3")], open_slots=slots)
    assert r.valid[0]["skill"] == "Python"
    assert r.valid[0]["competency"] == "Backend"


def test_exact_skill_match_beats_partial_match():
    slots = Counter({("B", "Python", "easy"): 1, ("B", "Python 3", "easy"): 1})
    r = validate_question_batch([_q("Python 3")], open_slots=slots)
    assert r.valid[0]["skill"] == "Python 3"
    assert slots[("B", "Python", "easy")] == 1


def test_wrong_difficulty_and_surplus_are_rejected():
    slots = Counter({("B", "Python", "easy"): 1})
    r = validate_question_batch([_q("Python", "hard"), _q("Python", "easy")], open_slots=slots)
    assert len(r.valid) == 1 and r.valid[0]["difficulty"] == "easy"
