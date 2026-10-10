"""InterviewIQ - Backend B End-to-End Demonstration Script

Demonstrates the complete Backend B lifecycle:
1. Loads mock job & candidate profile from data/mock_analysis.json (Backend A contract)
2. Computes deterministic difficulty distribution
3. Computes exact question budget using largest-remainder allocation
4. Generates questions via Gemini (supports --mock or live API)
5. Validates and displays formatted question plan
6. Demonstrates interactive question regeneration with an interviewer hint
7. Demonstrates cache hit performance

Usage:
    python demo_backend_b.py --mock    # Run locally with mock transport (no API key required)
    python demo_backend_b.py           # Run with live Gemini API (configured in .env)
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

import config
from llm.client import GeminiClient
from llm.prompts import QuestionBatchResponse, RawGeneratedQuestion, SingleQuestionResponse
from services.difficulty.difficulty_service import calculate_difficulty_mix
from services.question_gen.budget import build_question_budget
from services.question_gen.cache import InMemoryCache
from services.question_gen.generator import generate_plan_questions
from services.regenerate.regenerate_service import regenerate_question, RegenerationError


def get_mock_client() -> GeminiClient:
    """Mock client dynamically returning realistic technical questions matching requested slots."""
    import re

    bank = {
        ("Python", "easy"): (
            "What is the difference between mutable and immutable data types in Python, and how does it impact function argument passing?",
            ["Lists and dicts are mutable; strings and tuples are immutable", "Arguments are passed by object reference (call-by-sharing)", "Mutating an in-place argument affects the caller's object"]
        ),
        ("Python", "medium"): (
            "How would you process and clean a 15GB CSV file in Python on a worker machine with only 4GB of RAM?",
            ["Stream line-by-line using generators or chunksize in pandas/polars", "Select only required columns and downcast numeric datatypes", "Aggregate and write intermediate batches to disk", "Avoid loading entire file into memory"]
        ),
        ("Python", "hard"): (
            "How would you diagnose and resolve memory leaks caused by cyclic references and native C extensions in high-concurrency Python services?",
            ["Use tracemalloc and objgraph to inspect object allocation spikes", "Analyze gc.garbage and cyclic reference collector thresholds", "Inspect PyObject reference counting in C extension bindings", "Profile heap allocations with valgrind or memray"]
        ),
        ("FastAPI", "easy"): (
            "How do Pydantic models in FastAPI automatically handle incoming request payload validation and OpenAPI documentation generation?",
            ["Type hints define field types and default values", "Automatic 422 Unprocessable Entity responses on validation failure", "FastAPI extracts schema JSON directly from Pydantic models for Swagger/OpenAPI"]
        ),
        ("FastAPI", "medium"): (
            "Explain the difference between declaring an endpoint with 'async def' versus standard 'def' in FastAPI, and when you would choose each.",
            ["FastAPI executes 'def' endpoints in an external threadpool", "'async def' endpoints run directly on the event loop for non-blocking I/O", "Blocking CPU tasks or sync database drivers should not run directly in async def", "Async endpoints enable massive concurrency for I/O-bound microservices"]
        ),
        ("FastAPI", "hard"): (
            "How would you structure dependency injection and custom ASGI middleware in FastAPI to handle tenant isolation and database connection pooling under heavy load?",
            ["Use yield-based dependencies for connection acquisition and clean release", "Store request-scoped tenant context in contextvars", "Implement ASGI middleware for tenant header verification", "Manage async pool size and checkout timeouts to avoid exhaustion"]
        ),
        ("PostgreSQL", "easy"): (
            "What is the difference between WHERE and HAVING clauses in SQL, and in what scenario must you use each?",
            ["WHERE filters individual rows before any aggregations are computed", "HAVING filters groups of rows after GROUP BY aggregations", "HAVING can evaluate aggregate functions like COUNT, SUM, or AVG"]
        ),
        ("PostgreSQL", "medium"): (
            "Orders and customers are stored in separate relational tables. How would you construct an efficient query to find all active customers who have not placed an order in the last 90 days?",
            ["Use LEFT JOIN with NULL check or NOT EXISTS subquery", "Filter dates accurately on the order timestamp column", "Ensure join keys and date columns are indexed for performance", "Handle potential duplicate customer records properly"]
        ),
        ("PostgreSQL", "hard"): (
            "A mission-critical analytics query scanning a 50-million-row table slowed from 500ms to 45 seconds. How would you systematically diagnose and fix it?",
            ["Inspect execution plan with EXPLAIN (ANALYZE, BUFFERS)", "Check for sequential scans, table bloat, and missing composite indexes", "Analyze optimizer statistics and vacuum frequency", "Consider declarative partitioning by date range"]
        ),
        ("System Design", "easy"): (
            "What is the difference between horizontal scaling and vertical scaling, and what are the primary tradeoffs of each?",
            ["Vertical scaling adds CPU/RAM to a single server; horizontal scaling adds more servers", "Vertical scaling has hardware limits and single point of failure", "Horizontal scaling requires load balancers and stateless application design"]
        ),
        ("System Design", "medium"): (
            "How would you design a distributed URL shortening service (like Bitly) ensuring high availability and low read latency?",
            ["Base62 encoding of an auto-incrementing 64-bit ID", "Distributed caching layer (Redis) for frequently accessed URLs", "Replicated relational or NoSQL database for long-term mapping storage", "Read-heavy architecture with CDN caching"]
        ),
        ("System Design", "hard"): (
            "Design an idempotent payment webhook receiver to ensure no transaction is ever recorded twice despite retried incoming webhooks.",
            ["Extract and validate webhook idempotency ID or event UUID", "Use atomic distributed check-and-set or database unique constraint", "Return HTTP 200 immediately for previously recorded event IDs", "Maintain transactional outbox or message queue for downstream processing"]
        ),
    }

    def mock_transport(prompt, schema):
        if "REPLACE" in prompt or "regenerate" in str(schema):
            s_match = re.search(r"Skill:\s*'?([^'\n\r]+)'?", prompt)
            d_match = re.search(r"Required Difficulty:\s*(\w+)", prompt)
            target_skill = s_match.group(1).strip() if s_match else "Python"
            target_diff = d_match.group(1).strip().lower() if d_match else "medium"
            return SingleQuestionResponse(
                skill=target_skill,
                difficulty=target_diff,
                question=f"How would you design a thread-safe in-memory cache with LRU eviction and TTL support in {target_skill}?",
                key_points=[
                    "OrderedDict or doubly-linked list with hash map",
                    "threading.Lock or RLock for thread safety",
                    "Timestamp tracking for TTL expiration checks",
                    "Eviction of least-recently used entries when capacity reached"
                ]
            )

        # Batch generation: parse requested slots from prompt
        slot_matches = re.findall(r"- Skill:\s*'([^']+)'(?:[^|]*)\|\s*Difficulty:\s*(\w+)\s*\|\s*Count:\s*(\d+)", prompt)
        generated = []

        if slot_matches:
            for s_name, diff, count_str in slot_matches:
                cnt = int(count_str)
                for _ in range(cnt):
                    key = (s_name, diff)
                    if key in bank:
                        q_text, kps = bank[key]
                    else:
                        q_text = f"Explain practical implementation techniques and architecture for {s_name} at {diff} level in production."
                        kps = [f"Foundational {s_name} mechanisms", "Performance optimizations", "Failure handling"]
                    generated.append(RawGeneratedQuestion(
                        skill=s_name,
                        difficulty=diff,
                        question=q_text,
                        key_points=kps,
                    ))
        else:
            # Fallback default batch
            for (s_name, diff), (q_text, kps) in list(bank.items())[:5]:
                generated.append(RawGeneratedQuestion(skill=s_name, difficulty=diff, question=q_text, key_points=kps))

        return QuestionBatchResponse(questions=generated)

    return GeminiClient(transport=mock_transport)


async def run_demo():
    use_mock = "--mock" in sys.argv
    print("=" * 80)
    print("  InterviewIQ -- Backend B: AI Interview Question Generation")
    print(f"  Mode: {'MOCK SIMULATION (No API Key needed)' if use_mock else 'LIVE GEMINI API'}")
    print(f"  Active Model: {config.GEMINI_MODEL}")
    print("=" * 80)

    # 1. Load mock data from Backend A contract
    data_path = config.MOCK_ANALYSIS_PATH
    if not data_path.exists():
        print(f"Error: {data_path} not found!")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        analysis = json.load(f)

    job = analysis["job"]
    candidate = analysis["candidate"]
    competencies = analysis["competencies"]

    print(f"\n[1] Loaded Job & Candidate Profile from Backend A:")
    print(f"    - Target Role: {job['title']}")
    print(f"    - Description: {job['description_summary']}")
    print(f"    - Candidate Band: {candidate['band'].upper()} ({candidate['experience_years']} years exp)")
    print(f"    - Strengths: {', '.join(candidate['strengths'])}")
    print(f"    - Identified Gaps: {', '.join(candidate['gaps'])}")

    # 2. Difficulty distribution calculation
    diff_mix = calculate_difficulty_mix(candidate_band=candidate["band"])
    print(f"\n[2] Calculated Difficulty Distribution:")
    print(f"    - Easy: {diff_mix['easy']}% | Medium: {diff_mix['medium']}% | Hard: {diff_mix['hard']}%")

    # 3. Question budget allocation
    settings = config.GenerationSettings(
        interview_minutes=25,
        average_question_minutes=5,  # 5 questions total
        strategy="single_call",
        use_cache=True,
    )
    budget = build_question_budget(analysis, candidate_band=candidate["band"], settings=settings)
    print(f"\n[3] Computed Question Budget ({budget['total_questions']} Questions):")
    for alloc in budget["allocation"]:
        print(f"    - {alloc['competency']} -> {alloc['skill']}: {alloc['easy']} easy, {alloc['medium']} med, {alloc['hard']} hard (total {alloc['total']})")

    # 4. Generate Interview Questions
    client = get_mock_client() if use_mock else GeminiClient()
    cache = InMemoryCache()

    print(f"\n[4] Generating Interview Questions via Gemini...")
    t0 = time.monotonic()
    plan = await generate_plan_questions(
        job={**job, "competencies": competencies},
        candidate=candidate,
        settings=settings,
        client=client,
        cache=cache,
    )
    t_gen = time.monotonic() - t0

    print(f"    Generation Completed in {t_gen:.2f}s (Source: {plan.get('source', '').upper()})")
    
    # Check for question shortfall vs budget (D1)
    if plan.get("source") == "demo_cache" or plan.get("status") != "ready":
        print(f"    [WARNING] Status: {plan.get('status')}, Source: {plan.get('source')}, "
              f"{plan.get('total_questions')} of {plan.get('total_requested')} budgeted questions.")
        for n in plan.get("notes", []):
            print(f"      - {n}")
    else:
        print(f"    [OK] Exact budget met: {plan.get('total_questions')} of {plan.get('total_requested')} questions.")

    if plan.get("warnings"):
        print("    [WARNINGS]:")
        for warn in plan["warnings"]:
            print(f"      - {warn}")

    # Optional --save-demo-plan flag (D5) - saved BEFORE the regenerate step
    if "--save-demo-plan" in sys.argv:
        if plan.get("status") == "ready" and plan.get("source") == "generated":
            with open(config.DEMO_PLAN_PATH, "w", encoding="utf-8") as f:
                json.dump(plan, f, indent=2, ensure_ascii=False)
            print(f"    [INFO] Saved demo plan to {config.DEMO_PLAN_PATH}")
        else:
            print(f"    [WARNING] Skipped saving demo plan (status='{plan.get('status')}', source='{plan.get('source')}').")

    print("\n" + "-" * 80)
    print("  GENERATED INTERVIEW PLAN")
    print("-" * 80)
    for idx, q in enumerate(plan["questions"], 1):
        q_text = q.get("text") or q.get("question")
        print(f"\n[{idx}] [{q['competency']} | {q['skill']} | {q['difficulty'].upper()}]")
        print(f"    Question: {q_text}")
        print(f"    Expected Key Points:")
        for kp in q["key_points"]:
            print(f"      - {kp}")
        print(f"    Rationale: {q['rationale']}")

    # 5. Question Regeneration (D3)
    gen_ok = (plan.get("source") != "demo_cache" and plan.get("status") == "ready")
    regen_ok = False
    if plan.get("questions"):
        target_q = plan["questions"][0]
        q_target_text = target_q.get("text") or target_q.get("question")
        hint = "Make the scenario more practical and focus on concurrency"
        print("\n" + "-" * 80)
        print(f"  DEMONSTRATING QUESTION REGENERATION")
        print(f"  Replacing: [{target_q['id']}] '{q_target_text[:60]}...'")
        print(f"  Interviewer Hint: \"{hint}\"")
        print("-" * 80)

        feedback_records = []
        if not use_mock:
            await asyncio.sleep(2)  # Pause for free-tier rate limits

        t0_regen = time.monotonic()
        try:
            new_q = await regenerate_question(
                question=target_q,
                plan=plan,
                hint=hint,
                client=client,
                feedback_logger=feedback_records.append,
            )
            t_regen = time.monotonic() - t0_regen
            q_new_text = new_q.get("text") or new_q.get("question")
            print(f"\n    [OK] Successfully Regenerated in {t_regen:.2f}s:")
            print(f"    New Question: {q_new_text}")
            print(f"    Key Points:")
            for kp in new_q["key_points"]:
                print(f"      - {kp}")
            if feedback_records:
                print(f"    Feedback Metadata for Backend C: {feedback_records[0]}")
            regen_ok = True
        except RegenerationError as e:
            t_regen = time.monotonic() - t0_regen
            print(f"\n    [FAILED] {e}")
            regen_ok = False

    # 6. Demonstrating Cache Hit (D2)
    print("\n" + "-" * 80)
    print("  DEMONSTRATING CACHING PERFORMANCE")
    print("-" * 80)
    t0_cache = time.monotonic()
    cached_plan = await generate_plan_questions(
        job={**job, "competencies": competencies},
        candidate=candidate,
        settings=settings,
        client=client,
        cache=cache,
    )
    t_cache = time.monotonic() - t0_cache
    cache_ok = (cached_plan.get("source") == "cache")
    if cache_ok:
        print(f"    [OK] {cached_plan.get('total_questions')} questions served from cache in {t_cache*1000:.2f}ms (Source: CACHE)")
    else:
        print(f"    [SKIPPED] Not a cache hit (source: {cached_plan.get('source')})")

    # Final summary line (D4)
    print("\n" + "=" * 80)
    if gen_ok and regen_ok and cache_ok:
        print("  Demo complete: all subsystems OK")
    else:
        print("  Demo complete WITH PROBLEMS: see warnings above")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_demo())
