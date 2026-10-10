"""Unit tests for utils/validators.py."""
import pytest
from utils.validators import ValidatedQuestion, validate_question_batch


def test_validated_question_success():
    """Valid question passes Pydantic model validation."""
    data = {
        "skill": "Python",
        "difficulty": "medium",
        "question": "How would you handle asynchronous tasks using Celery and Redis in Python?",
        "key_points": [
            "Task broker configuration",
            "Result backend storage",
            "Error handling and retries"
        ]
    }
    model = ValidatedQuestion.model_validate(data)
    assert model.skill == "Python"
    assert model.difficulty == "medium"
    assert len(model.key_points) == 3


def test_short_question_fails():
    """Question under 25 characters must be rejected."""
    data = {
        "skill": "Python",
        "difficulty": "easy",
        "question": "What is Python?",  # < 25 chars
        "key_points": ["Interpreted language", "Dynamic typing"]
    }
    with pytest.raises(Exception):
        ValidatedQuestion.model_validate(data)


def test_invalid_difficulty_fails():
    """Difficulties outside 'easy', 'medium', 'hard' must be rejected."""
    data = {
        "skill": "Python",
        "difficulty": "impossible",
        "question": "Explain metaclasses and type creation in CPython internals in detail.",
        "key_points": ["type.__new__", "Class dict initialization"]
    }
    with pytest.raises(Exception):
        ValidatedQuestion.model_validate(data)


def test_insufficient_key_points_fails():
    """Question with fewer than 2 key points must fail validation."""
    data = {
        "skill": "Python",
        "difficulty": "medium",
        "question": "How do generators optimize memory usage when processing massive streams?",
        "key_points": ["Lazy evaluation"]  # Only 1 key point
    }
    with pytest.raises(Exception):
        ValidatedQuestion.model_validate(data)


def test_validate_question_batch_filters_duplicates():
    """Duplicate questions within a batch or matching exclusions must be filtered."""
    q_valid = {
        "skill": "Python",
        "difficulty": "medium",
        "question": "How do Python generators optimize memory usage when processing massive streams?",
        "key_points": ["Lazy evaluation", "yield keyword", "Constant memory consumption"]
    }
    # Duplicate question text
    q_duplicate = dict(q_valid)

    res = validate_question_batch([q_valid, q_duplicate], requested_skills={"Python"})
    assert len(res.valid) == 1
    assert len(res.invalid) == 1
    assert "duplicate" in res.errors[0].lower()


def test_validate_question_batch_filters_exclusions():
    """Questions present in exclusions list must be rejected."""
    q = {
        "skill": "SQL",
        "difficulty": "easy",
        "question": "What is the difference between INNER JOIN and LEFT JOIN in relational databases?",
        "key_points": ["INNER keeps matched rows", "LEFT keeps all left rows with NULL"]
    }
    exclusion = "What is the difference between INNER JOIN and LEFT JOIN in relational databases?"
    res = validate_question_batch([q], requested_skills={"SQL"}, exclusions=[exclusion])
    assert len(res.valid) == 0
    assert len(res.invalid) == 1


def test_validate_question_batch_rejects_wrong_difficulty_or_surplus_slots():
    """Questions with incorrect difficulty or surplus count must be rejected against open slots."""
    open_slots = {
        ("Backend", "Python", "medium"): 1,
        ("Backend", "Python", "hard"): 1,
    }
    batch = [
        # 1. Matches slot: Python hard
        {
            "skill": "Python",
            "difficulty": "hard",
            "question": "How do you diagnose memory leaks in Python high concurrency services?",
            "key_points": ["Use tracemalloc and objgraph", "Analyze gc.garbage", "Check C extension refcounts"]
        },
        # 2. Matches slot: Python medium
        {
            "skill": "Python",
            "difficulty": "medium",
            "question": "How do you process a 15GB CSV file in Python with only 4GB RAM?",
            "key_points": ["Stream line-by-line using generators", "Downcast datatypes", "Batch disk writes"]
        },
        # 3. Surplus: another Python medium (slot already claimed)
        {
            "skill": "Python",
            "difficulty": "medium",
            "question": "How does Python's asyncio event loop schedule coroutines?",
            "key_points": ["Single thread cooperative multitasking", "Tasks wrap futures", "await yields to loop"]
        },
        # 4. Wrong difficulty: Python easy (no easy slot budgeted)
        {
            "skill": "Python",
            "difficulty": "easy",
            "question": "What is the difference between list and tuple in Python?",
            "key_points": ["List is mutable", "Tuple is immutable"]
        },
        # 5. Wrong skill: PostgreSQL medium (no PostgreSQL slot)
        {
            "skill": "PostgreSQL",
            "difficulty": "medium",
            "question": "How do you optimize an indexed join query across large tables?",
            "key_points": ["Check EXPLAIN ANALYZE", "Ensure index on foreign key"]
        }
    ]

    res = validate_question_batch(batch, open_slots=open_slots)
    # Only the first 2 should be valid
    assert len(res.valid) == 2
    assert len(res.invalid) == 3
    assert res.valid[0]["difficulty"] == "hard"
    assert res.valid[1]["difficulty"] == "medium"
    assert "no open slot" in res.errors[0]
    assert open_slots[("Backend", "Python", "medium")] == 0
    assert open_slots[("Backend", "Python", "hard")] == 0
    assert res.remaining_slots == {}


def test_question_over_max_chars_is_rejected():
    """Questions exceeding MAX_QUESTION_CHARS must be rejected with ValueError."""
    long_q = "How would you design " + "a very scalable " * 30 + "distributed system in Python?"
    assert len(long_q) > 400
    data = {
        "skill": "Python",
        "difficulty": "medium",
        "question": long_q,
        "key_points": ["Valid point 1", "Valid point 2", "Valid point 3"],
    }
    with pytest.raises(Exception) as exc:
        ValidatedQuestion.model_validate(data)
    assert "too long" in str(exc.value).lower()


def test_key_point_over_max_chars_is_rejected():
    """Key points exceeding MAX_KEY_POINT_CHARS must be rejected with ValueError."""
    long_kp = "This key point explains in excessive detail " + "with repeated explanations " * 15
    assert len(long_kp) > 220
    data = {
        "skill": "Python",
        "difficulty": "medium",
        "question": "How would you design a thread-safe connection pool in Python?",
        "key_points": [long_kp, "Valid point 2", "Valid point 3"],
    }
    with pytest.raises(Exception) as exc:
        ValidatedQuestion.model_validate(data)
    assert "key points must be short" in str(exc.value).lower()


def test_normal_question_passes():
    """A standard sized question with concise key points must validate cleanly."""
    data = {
        "skill": "Python",
        "difficulty": "medium",
        "question": "How would you handle race conditions in shared state using threading.Lock in Python?",
        "key_points": [
            "Acquire lock before mutation",
            "Use context manager 'with lock' for safe release",
            "Minimize critical section duration",
        ],
    }
    model = ValidatedQuestion.model_validate(data)
    assert model.skill == "Python"
    assert model.difficulty == "medium"
    assert len(model.key_points) == 3


def test_copy_of_level_example_is_rejected():
    """Questions copying calibration examples must be rejected by validator."""
    data = {
        "skill": "FastAPI",
        "difficulty": "easy",
        "question": "What problem does Pydantic solve in FastAPI request handling?",
        "key_points": ["Request validation", "Schema generation", "Type enforcement"],
    }
    with pytest.raises(Exception) as exc:
        ValidatedQuestion.model_validate(data)
    assert "calibration" in str(exc.value).lower()

