import os
import sys

# Add project root and Backend directory to sys.path so services and models can be found
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "Backend")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.assembly import assemble_interview_plan
from models.schemas import PlanSettings

mock_questions = [
    {
        "competency": "Data Engineering",
        "skill": "SQL",
        "difficulty": "hard",
        "question": "How do you handle query optimization on partitioned tables?",
        "key_points": ["Index optimization", "Partition pruning"]
    },
    {
        "competency": "Data Engineering",
        "skill": "SQL",
        "difficulty": "easy",
        "question": "What is the difference between WHERE and HAVING?",
        "key_points": ["Row filter vs Group filter"]
    }
]

skills_map = {
    "SQL": {"level": "required", "weight": 0.4, "evidence": "Candidate has 3 years SQL experience"}
}

comp_weights = {"Data Engineering": 0.5, "Problem Solving": 0.5}

plan = assemble_interview_plan(
    job_id="job123",
    candidate_id="cand456",
    raw_questions=mock_questions,
    competency_weights=comp_weights,
    extracted_skills_map=skills_map,
    settings=PlanSettings()
)

print("--- Assembled Plan Questions (Sorted Easy to Hard) ---")
for q in plan["questions"]:
    print(f"[{q['difficulty'].upper()}] {q['question']}")
    print(f"Rationale: {q['rationale']}\n")

print("Coverage Summary:", plan["coverage_summary"])
