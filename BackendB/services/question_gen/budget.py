"""InterviewIQ - Question Budget Allocation Module

Determines total questions and allocates them proportionally across
competencies, skills, and difficulties using the Hare-Niemeyer (largest remainder)
rounding method to guarantee mathematical exactness.
"""
from __future__ import annotations

import math
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple, Union

import config
from services.difficulty.difficulty_service import (
    calculate_difficulty_mix,
    calculate_skill_difficulty_mix,
)


def calculate_total_questions(
    interview_duration_minutes: float,
    average_question_minutes: float = config.AVERAGE_QUESTION_MINUTES,
) -> int:
    """Calculates integer total question budget from interview duration."""
    if interview_duration_minutes <= 0 or average_question_minutes <= 0:
        return 1
    count = round(interview_duration_minutes / average_question_minutes)
    return max(1, count)


def largest_remainder_allocation(
    items: List[Tuple[Any, float]],  # List of (key, weight)
    total_count: int,
    guaranteed_keys: Optional[set] = None,
) -> Dict[Any, int]:
    """Allocates integer counts across items proportionally using largest remainder.

    Guarantees that the sum of allocated values equals total_count exactly.
    """
    if not items or total_count <= 0:
        return {k: 0 for k, _ in items}

    total_weight = sum(w for _, w in items)
    n_items = len(items)

    # Edge case: all weights are 0
    if total_weight <= 0:
        equal_share = total_count // n_items
        remainder = total_count % n_items
        alloc = {}
        for idx, (k, _) in enumerate(items):
            alloc[k] = equal_share + (1 if idx < remainder else 0)
        return alloc

    # Calculate exact quotas and integer floors
    allocations: Dict[Any, int] = {}
    remainders: List[Tuple[float, float, Any]] = []  # (fractional_part, weight, key)
    allocated_sum = 0

    guaranteed = guaranteed_keys or set()

    for k, w in items:
        quota = (w / total_weight) * total_count
        floor_val = math.floor(quota)
        frac = quota - floor_val
        allocations[k] = floor_val
        allocated_sum += floor_val
        remainders.append((frac, w, k))

    # Apply guarantee if items were allocated 0 but qualify for guarantee
    if total_count >= len(guaranteed):
        for k in guaranteed:
            if allocations.get(k, 0) == 0:
                allocations[k] = 1
                allocated_sum += 1

    deficit = total_count - allocated_sum

    # If we need more items, allocate to largest remainders
    if deficit > 0:
        # Sort by remainder descending, then by original weight descending for deterministic ties
        remainders.sort(key=lambda x: (x[0], x[1]), reverse=True)
        for i in range(deficit):
            chosen_key = remainders[i % len(remainders)][2]
            allocations[chosen_key] += 1

    # If we over-allocated due to guarantees, trim from smallest remainders with >0
    elif deficit < 0:
        remainders.sort(key=lambda x: (x[0], x[1]))
        excess = abs(deficit)
        for _, _, k in remainders:
            if excess <= 0:
                break
            if allocations[k] > 0:
                allocations[k] -= 1
                excess -= 1

    return allocations


def allocate_difficulties(
    count: int,
    difficulty_mix: Dict[str, int],
) -> Dict[str, int]:
    """Divides an integer skill question count into easy, medium, hard."""
    if count <= 0:
        return {"easy": 0, "medium": 0, "hard": 0}

    items = [
        ("easy", difficulty_mix.get("easy", 0)),
        ("medium", difficulty_mix.get("medium", 0)),
        ("hard", difficulty_mix.get("hard", 0)),
    ]
    return largest_remainder_allocation(items, count)


def build_question_budget(
    job_or_competencies: Union[Dict[str, Any], List[Dict[str, Any]]],
    candidate_band: str = config.DEFAULT_CANDIDATE_BAND,
    settings: Optional[config.GenerationSettings] = None,
    candidate_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generates the full question budget allocation plan.

    Args:
        job_or_competencies: Dict with 'competencies' or raw list of competencies.
        candidate_band: Candidate seniority level.
        settings: Optional GenerationSettings instance.
        candidate_profile: Optional candidate profile with evidence/strengths/gaps.

    Returns:
        Structured budget dict containing:
        - total_questions: int
        - allocation: List[Dict[str, Any]]
        - rows: Detailed flattened slot rows
        - budget_table: Human-readable markdown string
    """
    settings = settings or config.GenerationSettings()

    # Extract competencies
    if isinstance(job_or_competencies, dict):
        duration = job_or_competencies.get("interview_duration", settings.interview_minutes)
        avg_min = job_or_competencies.get("average_question_minutes", settings.average_question_minutes)
        raw_competencies = job_or_competencies.get("competencies", [])
    else:
        duration = settings.interview_minutes
        avg_min = settings.average_question_minutes
        raw_competencies = job_or_competencies

    total_questions = calculate_total_questions(duration, avg_min)

    # 1. Normalize competencies and extract weights
    competencies_data = []
    comp_weights = []
    total_comp_weight = 0.0

    for c in raw_competencies:
        c_name = c.get("name") or "General"
        c_weight = float(c.get("weight", 0) or 0)
        skills = c.get("skills", [])
        if not skills:
            skills = [{"name": c_name, "weight": max(1.0, c_weight)}]

        competencies_data.append({
            "name": c_name,
            "weight": c_weight,
            "skills": skills,
        })
        comp_weights.append((c_name, c_weight))
        total_comp_weight += c_weight

    if not competencies_data:
        # Fallback for empty competencies
        competencies_data = [{
            "name": "General Technical Competence",
            "weight": 100.0,
            "skills": [{"name": "Core Technical Skills", "weight": 100.0}],
        }]
        comp_weights = [(competencies_data[0]["name"], 100.0)]
        total_comp_weight = 100.0

    # Determine which competencies are important enough to guarantee >= 1 question
    guaranteed_comps = set()
    if total_comp_weight > 0 and total_questions >= len(competencies_data):
        for c_name, w in comp_weights:
            if (w / total_comp_weight) >= config.MIN_COMPETENCY_SHARE:
                guaranteed_comps.add(c_name)

    # 2. Allocate questions across competencies
    comp_allocation = largest_remainder_allocation(comp_weights, total_questions, guaranteed_comps)

    # 3. Base candidate difficulty mix
    base_diff_mix = calculate_difficulty_mix(
        candidate_band=candidate_band,
        override=settings.difficulty_override,
    )

    # Plan-level target difficulty budget (guarantees easy/medium/hard percentages across whole plan)
    plan_diff_budget = allocate_difficulties(total_questions, base_diff_mix)

    # 4. Allocate questions across skills within each competency
    skill_slots: List[Dict[str, Any]] = []

    for comp in competencies_data:
        c_name = comp["name"]
        comp_count = comp_allocation.get(c_name, 0)
        if comp_count <= 0:
            continue

        skills = comp["skills"]
        skill_weights = [(s.get("name", "Skill"), float(s.get("weight", 1) or 1)) for s in skills]
        skill_allocation = largest_remainder_allocation(skill_weights, comp_count)

        for s in skills:
            s_name = s.get("name", "Skill")
            s_count = skill_allocation.get(s_name, 0)
            if s_count <= 0:
                continue

            evidence = str(s.get("candidate_evidence") or s.get("evidence") or "").lower()
            s_weight = float(s.get("weight", 0) or 0)
            skill_share = (s_weight / total_comp_weight) if total_comp_weight > 0 else 0.0

            # Affinity scores for hard and easy
            if evidence in ("strong", "expert", "high", "verified"):
                hard_mult, easy_mult = 2.0, 0.2
            elif evidence in ("gap", "limited", "none", "weak", "missing"):
                hard_mult, easy_mult = 0.2, 2.0
            else:
                hard_mult, easy_mult = 1.0, 1.0

            for slot_i in range(s_count):
                skill_slots.append({
                    "competency": c_name,
                    "skill": s_name,
                    "skill_info": s,
                    "skill_share": skill_share,
                    "slot_index": slot_i,
                    "hard_score": hard_mult * (1.0 + skill_share) - (slot_i * 0.1),
                    "easy_score": easy_mult * (1.0 / max(0.05, skill_share)) - (slot_i * 0.1),
                    "difficulty": None,
                })

    # 5. Distribute plan-level difficulties across slots
    unassigned = list(range(len(skill_slots)))

    # Assign hard questions to highest hard_score
    num_hard = plan_diff_budget.get("hard", 0)
    unassigned.sort(key=lambda idx: skill_slots[idx]["hard_score"], reverse=True)
    for i in range(min(num_hard, len(unassigned))):
        chosen_idx = unassigned[i]
        skill_slots[chosen_idx]["difficulty"] = "hard"
    unassigned = [idx for idx in unassigned if skill_slots[idx]["difficulty"] is None]

    # Assign easy questions to highest easy_score
    num_easy = plan_diff_budget.get("easy", 0)
    unassigned.sort(key=lambda idx: skill_slots[idx]["easy_score"], reverse=True)
    for i in range(min(num_easy, len(unassigned))):
        chosen_idx = unassigned[i]
        skill_slots[chosen_idx]["difficulty"] = "easy"
    unassigned = [idx for idx in unassigned if skill_slots[idx]["difficulty"] is None]

    # Assign medium questions to all remaining slots
    for idx in unassigned:
        skill_slots[idx]["difficulty"] = "medium"

    # 6. Aggregate into final allocation and flattened rows
    allocation_map: Dict[Tuple[str, str], Dict[str, Any]] = OrderedDict()
    flattened_rows: List[Dict[str, Any]] = []

    for slot in skill_slots:
        key = (slot["competency"], slot["skill"])
        if key not in allocation_map:
            allocation_map[key] = {
                "competency": slot["competency"],
                "skill": slot["skill"],
                "easy": 0,
                "medium": 0,
                "hard": 0,
                "total": 0,
            }
        diff = slot["difficulty"]
        allocation_map[key][diff] += 1
        allocation_map[key]["total"] += 1

        flattened_rows.append({
            "competency": slot["competency"],
            "skill": slot["skill"],
            "difficulty": diff,
            "count": 1,
            "skill_info": slot["skill_info"],
            "skill_share": slot["skill_share"],
        })

    final_allocation = list(allocation_map.values())

    # Build human-readable summary table
    summary_lines = []
    summary_lines.append(f"Interview Duration: {duration} mins | Question Budget: {total_questions} questions")
    for item in final_allocation:
        summary_lines.append(
            f"- [{item['competency']}] {item['skill']}: {item['easy']} easy, {item['medium']} med, {item['hard']} hard (total {item['total']})"
        )

    return {
        "total_questions": total_questions,
        "allocation": final_allocation,
        "rows": flattened_rows,
        "budget_table": "\n".join(summary_lines),
    }
