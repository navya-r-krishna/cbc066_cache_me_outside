"""Integration unit tests for services/question_gen/generator.py."""
import pytest
import config
from llm.client import GeminiClient
from llm.prompts import QuestionBatchResponse, RawGeneratedQuestion
from services.question_gen.cache import InMemoryCache
from services.question_gen.generator import generate_plan_questions


import re


def make_mock_transport(return_questions=None):
    """Factory creating mock transport returning valid structured question batches."""
    def _transport(prompt, schema):
        if return_questions:
            return QuestionBatchResponse(questions=[RawGeneratedQuestion(**q) for q in return_questions])

        # Extract requested slots from prompt
        # Matches: - Skill: 'Python' (Competency: 'Cloud') | Difficulty: medium | Count: 1
        raw_matches = re.findall(
            r"Skill:\s*['\"]?([^'\"\(\n|]+?)['\"]?(?:\s*\([^)]*\))?\s*\|\s*Difficulty:\s*(\w+)(?:\s*\|\s*Count:\s*(\d+))?",
            prompt,
        )
        slot_matches = []
        for skill, diff, cnt_str in raw_matches:
            count = int(cnt_str) if cnt_str else 1
            for _ in range(count):
                slot_matches.append((skill.strip(), diff.strip().lower()))

        if not slot_matches:
            legacy = re.findall(r'(\d+)\s+question\(s\)\s+on\s+([^|\n]+)\s+at\s+(\w+)\s+difficulty', prompt)
            for cnt, skill, diff in legacy:
                for _ in range(int(cnt)):
                    slot_matches.append((skill.strip(), diff.strip().lower()))

        if not slot_matches:
            slot_matches = [("Python", "medium"), ("SQL", "hard")]

        qs = []
        diff_templates = {
            "easy": "Explain the fundamental syntax, standard library features, and builtin data structures when developing in {skill}.",
            "medium": "How would you implement distributed task workers, connection pooling, and reliable error handling in {skill}?",
            "hard": "How would you diagnose and resolve memory leaks, lock contention, and high concurrency performance bottlenecks in {skill}?",
        }
        for idx, (skill, diff) in enumerate(slot_matches, 1):
            tmpl = diff_templates.get(diff, diff_templates["medium"])
            qs.append({
                "skill": skill,
                "difficulty": diff,
                "question": tmpl.format(skill=skill) + f" (Context variant #{idx})",
                "key_points": [
                    f"Proficiency in {skill} core architecture",
                    f"Design considerations and trade-offs for {diff} scenarios",
                    "Monitoring, logging, and error handling mechanisms"
                ]
            })
        return QuestionBatchResponse(questions=[RawGeneratedQuestion(**q) for q in qs])
    return _transport


@pytest.mark.asyncio
async def test_generate_plan_questions_success():
    """Verify complete question plan generation with mock Gemini client."""
    job = {
        "title": "Senior Python Backend Engineer",
        "description_summary": "Lead development of high performance Python services and SQL databases.",
        "competencies": [
            {
                "name": "Backend",
                "weight": 50,
                "skills": [{"name": "Python", "weight": 50, "candidate_evidence": "strong"}]
            },
            {
                "name": "Database",
                "weight": 50,
                "skills": [{"name": "SQL", "weight": 50, "candidate_evidence": "limited"}]
            }
        ]
    }
    candidate = {
        "band": "intermediate",
        "experience_years": 3,
        "strengths": ["Python"],
        "gaps": ["Kafka"]
    }

    client = GeminiClient(transport=make_mock_transport())
    cache = InMemoryCache()
    settings = config.GenerationSettings(interview_minutes=10, average_question_minutes=5)  # 2 questions

    plan = await generate_plan_questions(job, candidate, settings, client=client, cache=cache)
    assert plan["status"] in ("ready", "success")
    assert len(plan["questions"]) == 2
    assert plan["source"] == "generated"
    for q in plan["questions"]:
        assert q["id"] is not None
        assert q["text"] is not None
        assert q["rationale"] is not None
        assert len(q["key_points"]) >= 2


@pytest.mark.asyncio
async def test_thin_jd_marked_assumed():
    """Thin JD with low info should synthesize competencies and mark questions assumed."""
    job = {
        "title": "Machine Learning Engineer",
        "low_info": True,
        "description_summary": "",
    }
    candidate = {"band": "beginner"}

    client = GeminiClient(transport=make_mock_transport([
        {
            "skill": "Core Technical Principles",
            "difficulty": "easy",
            "question": "What is the bias-variance tradeoff in machine learning and how do you mitigate overfitting?",
            "key_points": ["Bias is underfitting", "Variance is overfitting", "Cross validation and regularization"]
        }
    ]))

    plan = await generate_plan_questions(job, candidate, client=client, cache=InMemoryCache())
    assert len(plan["questions"]) > 0
    assert all(q["assumed"] is True for q in plan["questions"])
    assert "assumed" in plan["questions"][0]["rationale"].lower()


@pytest.mark.asyncio
async def test_cache_hit_avoids_llm_call():
    """Second identical call must be served from cache without invoking transport."""
    call_tracker = {"calls": 0}

    def counting_transport(prompt, schema):
        call_tracker["calls"] += 1
        return make_mock_transport()(prompt, schema)

    client = GeminiClient(transport=counting_transport)
    cache = InMemoryCache()
    job = {
        "title": "DevOps Engineer",
        "competencies": [{"name": "Cloud", "weight": 100, "skills": [{"name": "Python", "weight": 100}]}]
    }
    candidate = {"band": "intermediate"}
    settings = config.GenerationSettings(interview_minutes=10, average_question_minutes=5)

    # First call - populates cache
    plan1 = await generate_plan_questions(job, candidate, settings, client=client, cache=cache)
    assert call_tracker["calls"] == 1
    assert plan1["source"] == "generated"

    # Second call - hit cache
    plan2 = await generate_plan_questions(job, candidate, settings, client=client, cache=cache)
    assert call_tracker["calls"] == 1  # No new call
    assert plan2["source"] == "cache"


@pytest.mark.asyncio
async def test_outage_fallback_to_demo_plan():
    """When Gemini transport fails, generator serves demo plan fallback."""
    def broken_transport(prompt, schema):
        raise RuntimeError("Google API 503 Outage")

    client = GeminiClient(transport=broken_transport, max_retries=1)
    job = {"title": "Software Engineer"}
    candidate = {"band": "intermediate"}

    plan = await generate_plan_questions(job, candidate, client=client, cache=InMemoryCache())
    assert plan["source"] == "demo_cache"
    assert len(plan["questions"]) >= 5
    assert any("demo plan" in n.lower() for n in plan["notes"])


@pytest.mark.asyncio
async def test_candidate_mongodb_history_integration():
    """Candidates history from MongoDB collection schema should be passed to prompt exclusions."""
    captured_prompt = {"prompt": ""}

    def inspect_transport(prompt, schema):
        captured_prompt["prompt"] = prompt
        return make_mock_transport()(prompt, schema)

    client = GeminiClient(transport=inspect_transport)
    job = {
        "id": "job_001",
        "title": "Backend Dev",
        "competencies": [{"name": "Core", "weight": 100, "skills": [{"name": "Python", "weight": 100}]}]
    }
    # Matching MongoDB candidates collection schema
    candidate = {
        "id": "cand_001",
        "name": "Candidate X",
        "band": "intermediate",
        "history": [
            {
                "question": "What is the difference between list and tuple in Python?",
                "answer": "Lists are mutable and tuples are immutable.",
                "plan_id": "plan_old_01"
            }
        ]
    }
    settings = config.GenerationSettings(interview_minutes=5, average_question_minutes=5)

    plan = await generate_plan_questions(job, candidate, settings, client=client, cache=InMemoryCache())
    assert "What is the difference between list and tuple in Python?" in captured_prompt["prompt"]
    assert plan["job_id"] == "job_001"
    assert plan["candidate_id"] == "cand_001"
    assert plan["candidate_name"] == "Candidate X"
    assert plan["status"] in ("ready", "partial")
    assert "coverage" in plan
    for q in plan["questions"]:
        assert "text" in q
        assert "question" in q


@pytest.mark.asyncio
async def test_generation_over_long_question_triggers_retry_for_slot():
    """An over-long question fails validation, leaving its slot open and triggering retry for only that slot."""
    calls = []

    def mock_retry_transport(prompt, schema):
        calls.append(prompt)
        if len(calls) == 1:
            # First call: return one valid question and one over-long (>400 chars) question
            return QuestionBatchResponse(questions=[
                RawGeneratedQuestion(
                    skill="Python",
                    difficulty="hard",
                    question="How would you design " + "a very large and excessively verbose " * 15 + "system?",
                    key_points=["Point 1", "Point 2", "Point 3"],
                ),
                RawGeneratedQuestion(
                    skill="SQL",
                    difficulty="medium",
                    question="How would you optimize a slow database query using indexes in PostgreSQL?",
                    key_points=["Explain analyze", "Index types", "Vacuum"],
                ),
            ])
        else:
            # Second call (retry): return a valid short question for the retried slot
            return QuestionBatchResponse(questions=[
                RawGeneratedQuestion(
                    skill="Python",
                    difficulty="hard",
                    question="How do generators optimize memory usage when processing massive streams?",
                    key_points=["Lazy evaluation", "Constant memory usage", "Yield keyword"],
                ),
            ])

    client = GeminiClient(transport=mock_retry_transport)
    job = {
        "title": "Backend Engineer",
        "competencies": [
            {
                "name": "Backend",
                "weight": 50,
                "skills": [{"name": "Python", "weight": 50}],
            },
            {
                "name": "Database",
                "weight": 50,
                "skills": [{"name": "SQL", "weight": 50}],
            },
        ],
    }
    candidate = {"band": "intermediate"}
    settings = config.GenerationSettings(interview_minutes=10, average_question_minutes=5)

    plan = await generate_plan_questions(job, candidate, settings, client=client, cache=InMemoryCache())
    # Verify retry occurred: calls == 2
    assert len(calls) == 2
    # Verify that call 2 requested ONLY the missing Python slot, NOT SQL
    assert "- Skill: 'Python'" in calls[1]
    assert "- Skill: 'SQL'" not in calls[1]
    assert "You MUST generate exactly 1 questions" in calls[1]
    # Verify complete plan was generated
    assert plan["status"] == "ready"
    assert len(plan["questions"]) == 2
    skills = {q["skill"] for q in plan["questions"]}
    assert "Python" in skills
    assert "SQL" in skills

