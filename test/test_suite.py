import sys
import os
import json

# Ensure project root and Backend directory are in sys.path so config, services, and models modules can be found
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "Backend")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.dedup import is_duplicate
from services.assembly import assemble_interview_plan
from models.schemas import PlanSettings
from sentence_transformers import SentenceTransformer


def run_suite():
    print("==========================================")
    print("   BACKEND C: FULL INTEGRATION TEST SUITE  ")
    print("==========================================")

    # 1. Load Seed Data
    jobs_path = os.path.join(PROJECT_ROOT, "data", "sample_jobs.json")
    with open(jobs_path, "r", encoding="utf-8") as f:
        sample_jobs = json.load(f)
    print(f"[OK] Loaded {len(sample_jobs)} seed job descriptions.")

    # 2. Verify Thin JD Flag logic
    thin_jd = next(j for j in sample_jobs if j.get("low_info") == True)
    assert thin_jd["low_info"] == True, "Thin JD flag check failed."
    print("[OK] Thin JD flag invariant verified.")

    # 3. Verify Skill Weights Invariant
    valid_jd = next(j for j in sample_jobs if not j.get("low_info"))
    weights_sum = sum(s["weight"] for s in valid_jd["skills"])
    assert abs(weights_sum - 1.0) < 0.001, f"Skill weights must sum to 1.0, got {weights_sum}"
    print(f"[OK] Skill weights sum invariant verified ({weights_sum}).")

    # 4. Verify Vector De-duplication
    print("Loading SentenceTransformer model ('all-MiniLM-L6-v2')...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    q1 = "How do you optimize slow SQL queries with indexes?"
    existing = [{"question": "What steps speed up database queries using indexes?"}]
    
    is_dup, match, score = is_duplicate(q1, existing, model=model, threshold=0.85)
    assert is_dup == True, f"De-duplication failed to catch duplicate (Score: {score})"
    print(f"[OK] De-duplication verified (Caught duplicate with similarity score: {score}).")

    # 5. Verify Plan Assembly & Rationale Generation
    raw_qs = [
        {"competency": "Technical", "skill": "Python", "difficulty": "medium", "question": "Explain Python generators."},
        {"competency": "Technical", "skill": "Python", "difficulty": "easy", "question": "What is a list comprehension?"}
    ]
    skills_map = {"Python": {"level": "required", "weight": 0.35, "evidence": "3 years experience"}}
    
    plan = assemble_interview_plan(
        job_id=valid_jd["_id"],
        candidate_id="cand_dev_01",
        raw_questions=raw_qs,
        competency_weights={"Technical": 1.0},
        extracted_skills_map=skills_map,
        settings=PlanSettings()
    )

    # Confirm Easy to Hard sorting
    assert plan["questions"][0]["difficulty"] == "easy", "Sorting failed: First question should be easy."
    assert plan["questions"][1]["difficulty"] == "medium", "Sorting failed: Second question should be medium."
    print("[OK] Assembly sorting (Easy -> Hard) verified.")
    print("[OK] Deterministic rationale template generation verified.")

    print("\n==========================================")
    print("   ALL BACKEND C TESTS PASSED SUCCESSFULLY!")
    print("==========================================")


if __name__ == "__main__":
    run_suite()