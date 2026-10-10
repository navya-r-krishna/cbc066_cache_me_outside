"""Unit tests for services/question_gen/cache.py."""
import tempfile
import time
from pathlib import Path
import pytest
from services.question_gen.cache import (
    InMemoryCache,
    FileCache,
    generate_cache_key,
    load_demo_plan,
)


def test_generate_cache_key_deterministic():
    """Identical parameters produce identical hash keys regardless of dict ordering."""
    k1 = generate_cache_key(role="Backend Engineer", minutes=30, band="intermediate")
    k2 = generate_cache_key(band="intermediate", role="Backend Engineer", minutes=30)
    assert k1 == k2
    assert len(k1) == 64  # SHA-256


def test_in_memory_cache_set_get():
    """InMemoryCache correctly stores and returns payloads."""
    cache = InMemoryCache(default_ttl=3600)
    data = {"plan": "sample_data", "count": 5}
    cache.set("key1", data)

    cached = cache.get("key1")
    assert cached == data
    assert cache.get("nonexistent") is None


def test_in_memory_cache_ttl_expiration():
    """Items past TTL return None and are cleared."""
    cache = InMemoryCache(default_ttl=1)  # 1 second TTL
    cache.set("key1", {"status": "ok"}, ttl_seconds=1)
    assert cache.get("key1") is not None

    time.sleep(1.1)
    assert cache.get("key1") is None


def test_file_cache_operations():
    """FileCache correctly persists and cleans up JSON records."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cache = FileCache(cache_dir=tmp_dir, default_ttl=3600)
        cache.set("k1", {"foo": "bar"})

        assert cache.get("k1") == {"foo": "bar"}
        assert (Path(tmp_dir) / "k1.json").exists()

        cache.delete("k1")
        assert cache.get("k1") is None
        assert not (Path(tmp_dir) / "k1.json").exists()


def test_load_demo_plan():
    """Verify demo plan loads and contains expected demo questions."""
    plan = load_demo_plan()
    assert plan is not None
    assert "questions" in plan
    assert len(plan["questions"]) >= 5
    assert plan["source"] == "demo_cache"


def test_cache_key_sensitivity():
    """Verify changing difficulty_override or gaps changes the key, while changing candidate name or resume does not."""
    base_candidate = {
        "name": "Alice Smith",
        "resume": "10 years experience building distributed microservices",
        "strengths": ["Python", "FastAPI"],
        "gaps": ["Kafka"],
    }
    k_base = generate_cache_key(
        role="Backend Engineer",
        minutes=30,
        band="intermediate",
        candidate=base_candidate,
        difficulty_override="medium",
    )

    # 1. Changing candidate name must NOT change the cache key
    cand_diff_name = dict(base_candidate, name="Bob Jones")
    k_name = generate_cache_key(
        role="Backend Engineer",
        minutes=30,
        band="intermediate",
        candidate=cand_diff_name,
        difficulty_override="medium",
    )
    assert k_base == k_name, "Cache key must not change when only candidate name changes"

    # 2. Changing candidate resume text must NOT change the cache key
    cand_diff_resume = dict(base_candidate, resume="Different resume summary entirely")
    k_resume = generate_cache_key(
        role="Backend Engineer",
        minutes=30,
        band="intermediate",
        candidate=cand_diff_resume,
        difficulty_override="medium",
    )
    assert k_base == k_resume, "Cache key must not change when candidate resume text changes"

    # 3. Changing difficulty_override MUST change the cache key
    k_diff_override = generate_cache_key(
        role="Backend Engineer",
        minutes=30,
        band="intermediate",
        candidate=base_candidate,
        difficulty_override="hard",
    )
    assert k_base != k_diff_override, "Cache key must change when difficulty_override changes"

    # 4. Changing candidate gaps MUST change the cache key
    cand_diff_gaps = dict(base_candidate, gaps=["PostgreSQL", "Redis"])
    k_gaps = generate_cache_key(
        role="Backend Engineer",
        minutes=30,
        band="intermediate",
        candidate=cand_diff_gaps,
        difficulty_override="medium",
    )
    assert k_base != k_gaps, "Cache key must change when candidate gaps change"

