from typing import List, Dict, Any, Tuple
import logging
from models.schemas import InterviewPlan, QuestionItem, QuestionStatus, PlanSettings

logger = logging.getLogger("uvicorn")


def generate_rationale_from_template(
    skill: str,
    skill_level: str,
    skill_weight: float,
    candidate_evidence: str
) -> str:
    """
    Constructs a deterministic, explainable rationale without calling an LLM.
    """
    weight_desc = "high weight" if skill_weight >= 0.25 else ("medium weight" if skill_weight >= 0.15 else "low weight")
    level_str = skill_level.capitalize() if skill_level else "Required"
    
    evidence_str = candidate_evidence if candidate_evidence else "No specific experience listed in resume."
    
    return f"Tests {skill} ({level_str.lower()}, {weight_desc}). Candidate evidence: {evidence_str}"


def compute_coverage_summary(
    questions: List[Dict[str, Any]],
    competency_weights: Dict[str, float]
) -> Tuple[Dict[str, float], List[str]]:
    """
    Computes the share of questions per competency against its target weight.
    Returns:
        (coverage_percentage_map, list_of_under_covered_competencies)
    """
    total_q = len(questions)
    if total_q == 0:
        return {}, list(competency_weights.keys())

    counts = {}
    for q in questions:
        comp = q.get("competency", "General")
        counts[comp] = counts.get(comp, 0) + 1

    coverage_map = {}
    under_covered = []

    for comp, target_weight in competency_weights.items():
        actual_share = counts.get(comp, 0) / total_q
        coverage_map[comp] = round(actual_share, 2)
        
        # Flag if actual question proportion is significantly lower than target weight
        if actual_share < (target_weight * 0.7):
            under_covered.append(comp)

    return coverage_map, under_covered


def assemble_interview_plan(
    job_id: str,
    candidate_id: str,
    raw_questions: List[Dict[str, Any]],
    competency_weights: Dict[str, float],
    extracted_skills_map: Dict[str, Dict[str, Any]],
    settings: PlanSettings
) -> Dict[str, Any]:
    """
    Assembles, orders, fills rationales, and attaches coverage metadata to the plan.
    """
    difficulty_order = {"easy": 1, "medium": 2, "hard": 3}

    assembled_questions = []

    for q in raw_questions:
        skill_name = q.get("skill", "")
        skill_facts = extracted_skills_map.get(skill_name, {})
        
        # 1. Fill rationale template if empty
        if not q.get("rationale"):
            q["rationale"] = generate_rationale_from_template(
                skill=skill_name,
                skill_level=skill_facts.get("level", "required"),
                skill_weight=skill_facts.get("weight", 0.2),
                candidate_evidence=skill_facts.get("evidence", "Resume match")
            )

        # 2. Ensure default status
        q["status"] = q.get("status", QuestionStatus.PENDING)
        assembled_questions.append(q)

    # 3. Sort questions within competency from Easy to Hard
    assembled_questions.sort(
        key=lambda x: (x.get("competency", ""), difficulty_order.get(x.get("difficulty", "medium"), 2))
    )

    # 4. Compute coverage summary
    coverage_map, under_covered = compute_coverage_summary(assembled_questions, competency_weights)

    # 5. Construct final dictionary ready for MongoDB insertion
    plan_dict = {
        "job_id": job_id,
        "candidate_id": candidate_id,
        "settings": settings.model_dump(),
        "questions": assembled_questions,
        "coverage_summary": coverage_map,
        "under_covered_competencies": under_covered,
        "status": "created"
    }

    return plan_dict
