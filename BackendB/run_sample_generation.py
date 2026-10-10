"""Generate interview question plans for Frontend React Engineer and Data Analyst roles from sample_jobs.json."""
import asyncio
import json
import time
from pathlib import Path

import config
from llm.client import GeminiClient
from services.question_gen.generator import generate_plan_questions


async def main():
    sample_jobs_path = Path("data/sample_jobs.json")
    with open(sample_jobs_path, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    react_job = next(j for j in jobs if "react" in j["title"].lower())
    analyst_job = next(j for j in jobs if "analyst" in j["title"].lower())

    cand_react = {
        "id": "cand_react_01",
        "name": "Jordan Lee",
        "band": "intermediate",
        "experience_years": 3,
        "strengths": ["React", "TypeScript"],
        "gaps": ["Web Performance"],
        "history": [],
    }

    cand_analyst = {
        "id": "cand_analyst_01",
        "name": "Morgan Davis",
        "band": "intermediate",
        "experience_years": 3,
        "strengths": ["SQL", "Data Visualization"],
        "gaps": ["Data Modeling"],
        "history": [],
    }

    settings = config.GenerationSettings(
        interview_minutes=25,
        average_question_minutes=5,
        strategy="single_call",
        use_cache=False,
    )

    client = GeminiClient(timeout=60.0)

    # --- Role 1: Frontend React Engineer ---
    print("=" * 80)
    print("  ROLE 1: Frontend React Engineer")
    print(f"  Model: {config.GEMINI_MODEL}")
    print("=" * 80)

    t0 = time.monotonic()
    plan_react = await generate_plan_questions(
        job=react_job,
        candidate=cand_react,
        settings=settings,
        client=client,
    )
    t_react = time.monotonic() - t0

    print(f"Generation completed in {t_react:.2f}s | Status: {plan_react.get('status')} | Source: {plan_react.get('source')}")
    print(f"Total Questions: {len(plan_react.get('questions', []))} of {plan_react.get('total_requested')}\n")

    for idx, q in enumerate(plan_react.get("questions", []), 1):
        print(f"[{idx}] [{q['competency']} | {q['skill']} | {q['difficulty'].upper()}]")
        print(f"    Question: {q['text']}")
        print("    Expected Key Points:")
        for kp in q["key_points"]:
            print(f"      - {kp}")
        print(f"    Rationale: {q['rationale']}\n")

    # Brief delay for rate limit friendly execution
    await asyncio.sleep(2)

    # --- Role 2: Data Analyst ---
    print("=" * 80)
    print("  ROLE 2: Data Analyst")
    print(f"  Model: {config.GEMINI_MODEL}")
    print("=" * 80)

    t0 = time.monotonic()
    plan_analyst = await generate_plan_questions(
        job=analyst_job,
        candidate=cand_analyst,
        settings=settings,
        client=client,
    )
    t_analyst = time.monotonic() - t0

    print(f"Generation completed in {t_analyst:.2f}s | Status: {plan_analyst.get('status')} | Source: {plan_analyst.get('source')}")
    print(f"Total Questions: {len(plan_analyst.get('questions', []))} of {plan_analyst.get('total_requested')}\n")

    for idx, q in enumerate(plan_analyst.get("questions", []), 1):
        print(f"[{idx}] [{q['competency']} | {q['skill']} | {q['difficulty'].upper()}]")
        print(f"    Question: {q['text']}")
        print("    Expected Key Points:")
        for kp in q["key_points"]:
            print(f"      - {kp}")
        print(f"    Rationale: {q['rationale']}\n")

    # Save outputs to scratch or data for reference
    out_dir = Path("data")
    with open(out_dir / "generated_react_plan.json", "w", encoding="utf-8") as f:
        json.dump(plan_react, f, indent=2, ensure_ascii=False)
    with open(out_dir / "generated_data_analyst_plan.json", "w", encoding="utf-8") as f:
        json.dump(plan_analyst, f, indent=2, ensure_ascii=False)
    print("Saved plans to data/generated_react_plan.json and data/generated_data_analyst_plan.json")


if __name__ == "__main__":
    asyncio.run(main())
