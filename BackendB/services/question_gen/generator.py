"""InterviewIQ - Question Generation Service

Orchestrates the entire question generation pipeline: budget allocation,
prompt generation, Gemini API interaction, validation, replacement passes,
deduplication adapter integration, caching, and demo plan fallbacks.
"""
from __future__ import annotations

import asyncio
import copy
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import config
from llm.client import GeminiClient, LLMClientError
from llm.prompts import (
    PROMPT_VERSION,
    QuestionBatchResponse,
    build_question_generation_prompt,
)
from services.difficulty.difficulty_service import calculate_difficulty_mix
from services.question_gen.budget import build_question_budget
from services.question_gen.cache import (
    BaseCache,
    InMemoryCache,
    generate_cache_key,
    load_demo_plan,
)
from utils.validators import validate_question_batch

logger = logging.getLogger("interviewiq.generator")

# One shared cache for the whole process. (Before, a NEW cache was built on every call, so it never hit.)
_DEFAULT_CACHE = InMemoryCache()


def _friendly_error(err: Exception) -> str:
    """Short, UI-safe message. The raw provider error (quota JSON, links) stays in the logs only."""
    msg = str(err).lower()
    if "429" in msg or "resource_exhausted" in msg or "quota" in msg:
        return "The AI service has reached its usage limit. Please try again later."
    if "503" in msg or "unavailable" in msg:
        return "The AI service is busy right now. Please try again shortly."
    if "timeout" in msg or "timed out" in msg:
        return "The AI service took too long to respond."
    return "The AI service could not complete the request."


def default_dedup_checker(new_text: str, existing_texts: List[str]) -> bool:
    """Default fallback deduplication adapter if Backend C adapter is not provided."""
    import re
    norm_new = set(re.findall(r"\w+", new_text.lower()))
    if not norm_new:
        return False
    for ex in existing_texts:
        norm_ex = set(re.findall(r"\w+", ex.lower()))
        if not norm_ex:
            continue
        # Jaccard word similarity threshold
        intersection = len(norm_new.intersection(norm_ex))
        union = len(norm_new.union(norm_ex))
        if union > 0 and (intersection / union) > 0.75:
            return True
    return False


def make_rationale(
    question_dict: Dict[str, Any],
    skill_info: Dict[str, Any],
    skill_share: float,
    is_assumed: bool = False,
) -> str:
    """Deterministically generates a professional rationale for asking the question."""
    skill = question_dict.get("skill", "General")
    competency = question_dict.get("competency", "Role Competency")
    difficulty = question_dict.get("difficulty", "medium")

    if is_assumed:
        return f"Assumed core competency for the role ({competency} - {skill}). Calibrated at {difficulty} difficulty."

    req_level = skill_info.get("requirement_level") or skill_info.get("requirement") or "required"
    evidence = skill_info.get("candidate_evidence") or skill_info.get("evidence")

    weight_pct = f"{int(round(skill_share * 100))}%" if skill_share > 0 else "standard"
    evidence_str = f"with {evidence} candidate evidence" if evidence else "to assess unverified candidate experience"

    return (
        f"Tests {skill} under {competency}: {req_level} skill ({weight_pct} role weighting), "
        f"{evidence_str}. Calibrated at {difficulty} difficulty."
    )


def _normalize_input_job(job_input: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    """Ensures job data conforms to internal structures and detects thin JDs."""
    job = copy.deepcopy(job_input)
    title = job.get("title") or "Technical Candidate"
    summary = job.get("description_summary") or job.get("summary") or ""
    is_thin = bool(job.get("low_info") or (len(summary) < 30 and not job.get("competencies")))

    if is_thin and not job.get("competencies"):
        # Synthesize standard assumed competencies for the role
        job["competencies"] = [
            {
                "name": f"{title} Core Skills",
                "weight": 70,
                "skills": [{"name": "Core Technical Principles", "weight": 70, "requirement_level": "assumed"}],
            },
            {
                "name": "Problem Solving & Architecture",
                "weight": 30,
                "skills": [{"name": "System Design & Troubleshooting", "weight": 30, "requirement_level": "assumed"}],
            },
        ]

    return job, is_thin


async def _fill_slots_batch(
    client: GeminiClient,
    job_title: str,
    job_summary: str,
    candidate: Dict[str, Any],
    slots: List[Dict[str, Any]],
    exclusions: List[str],
) -> List[Dict[str, Any]]:
    """Calls Gemini to fill a list of question slots and returns raw question dicts."""
    prompt = build_question_generation_prompt(
        job_title=job_title,
        job_summary=job_summary,
        requested_slots=slots,
        candidate_band=candidate.get("band", config.DEFAULT_CANDIDATE_BAND),
        candidate_strengths=candidate.get("strengths", []),
        candidate_gaps=candidate.get("gaps", []),
        exclusions=exclusions,
    )

    batch_resp = await client.generate_structured(prompt, QuestionBatchResponse, purpose="generate_questions")
    return [q.model_dump() for q in batch_resp.questions]


async def generate_plan_questions(
    job: Dict[str, Any],
    candidate: Dict[str, Any],
    settings: Optional[config.GenerationSettings] = None,
    *,
    client: Optional[GeminiClient] = None,
    dedup: Optional[Callable[[str, List[str]], bool]] = None,
    cache: Optional[BaseCache] = None,
    history: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generates a complete structured interview plan.

    Args:
        job: Job specification dict conforming to Backend A contract.
        candidate: Candidate profile dict conforming to Backend A contract.
        settings: GenerationSettings instance.
        client: GeminiClient instance (or mock client).
        dedup: Optional duplicate detection function from Backend C.
        cache: Optional BaseCache implementation.
        history: Questions previously asked to this candidate.

    Returns:
        Structured plan dict matching the Backend B output specification.
    """
    settings = settings or config.GenerationSettings()
    client = client or GeminiClient()
    dedup_fn = dedup or default_dedup_checker
    cache_store = cache if cache is not None else _DEFAULT_CACHE

    # Extract candidate history (supports strings or objects from MongoDB candidates.history)
    raw_history = history if history is not None else candidate.get("history", [])
    history_list: List[str] = []
    for h in raw_history:
        if isinstance(h, str) and h.strip():
            history_list.append(h.strip())
        elif isinstance(h, dict):
            q_text = h.get("question") or h.get("text") or h.get("question_text", "")
            if q_text and q_text.strip():
                history_list.append(q_text.strip())

    notes: List[str] = []
    warnings: List[str] = []

    # 1. Normalize job and check for thin descriptions
    normalized_job, is_thin_jd = _normalize_input_job(job)
    job_title = normalized_job.get("title", "Technical Candidate")
    job_summary = normalized_job.get("description_summary", "")

    # 2. Check Cache
    cache_key = ""
    if settings.use_cache:
        cache_key = generate_cache_key(
            job=normalized_job,
            band=candidate.get("band", ""),
            minutes=settings.interview_minutes,
            model=client.model,
            exclusions=history_list,
            difficulty_override=settings.difficulty_override,
            strategy=settings.strategy,
            candidate_strengths=candidate.get("strengths", []),
            candidate_gaps=candidate.get("gaps", []),
            prompt_version=PROMPT_VERSION,
        )
        cached_result = cache_store.get(cache_key)
        if cached_result:
            logger.info("Serving plan from cache for job '%s'", job_title)
            cached_result = copy.deepcopy(cached_result)   # never mutate the stored object
            cached_result["source"] = "cache"
            return cached_result

    # 3. Calculate Question Budget
    budget = build_question_budget(
        job_or_competencies=normalized_job,
        candidate_band=candidate.get("band", config.DEFAULT_CANDIDATE_BAND),
        settings=settings,
        candidate_profile=candidate,
    )
    total_requested = budget["total_questions"]
    all_rows = budget["rows"]

    from collections import Counter
    open_slots: Counter = Counter()
    for r in all_rows:
        open_slots[(r["competency"], r["skill"], r["difficulty"])] += r["count"]

    # 4. Partition requests based on strategy
    # Strategy: "single_call" (one batch for all competencies) or "per_competency"
    strategy = settings.strategy or config.GENERATION_STRATEGY
    batch_groups: List[List[Dict[str, Any]]] = []

    if strategy == "single_call" or len(all_rows) <= 4:
        batch_groups.append(all_rows)
    else:
        # Group by competency
        by_comp: Dict[str, List[Dict[str, Any]]] = {}
        for r in all_rows:
            by_comp.setdefault(r["competency"], []).append(r)
        batch_groups = list(by_comp.values())

    # 5. Execute Initial LLM Calls with concurrency control
    sem = asyncio.Semaphore(settings.max_concurrent_calls)
    collected_raw_questions: List[Dict[str, Any]] = []
    llm_errors: List[Exception] = []

    async def _fetch_group(slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        async with sem:
            try:
                return await _fill_slots_batch(
                    client=client,
                    job_title=job_title,
                    job_summary=job_summary,
                    candidate=candidate,
                    slots=slots,
                    exclusions=history_list,
                )
            except LLMClientError as err:
                logger.warning("LLM call failed for slots group: %s", err)
                notes.append(_friendly_error(err))
                llm_errors.append(err)
                return []

    fetch_tasks = [_fetch_group(group) for group in batch_groups]
    group_results = await asyncio.gather(*fetch_tasks)
    for g in group_results:
        collected_raw_questions.extend(g)

    # 6. Validate & Claim Slots
    seen_texts: List[str] = list(history_list)
    val_result = validate_question_batch(
        raw_questions=collected_raw_questions,
        open_slots=open_slots,
        exclusions=seen_texts,
    )

    kept_questions: List[Dict[str, Any]] = []
    for q in val_result.valid:
        if dedup_fn(q["question"], seen_texts):
            warnings.append(f"Dropped duplicate question testing {q['skill']}")
            slot_key = (q.get("competency", "Core"), q["skill"], q["difficulty"])
            open_slots[slot_key] += 1  # Refund slot
        else:
            kept_questions.append(q)
            seen_texts.append(q["question"])

    # 7. Targeted Retry for Missing Slots (Up to MAX_REPLACEMENT_ROUNDS)
    # If every first-round call failed (quota/outage), retrying only burns more quota.
    llm_down = bool(llm_errors) and not collected_raw_questions
    if sum(open_slots.values()) > 0 and not is_thin_jd and not llm_down:
        for round_num in range(1, config.MAX_REPLACEMENT_ROUNDS + 1):
            missing_slots = [
                {"competency": c, "skill": s, "difficulty": d, "count": cnt}
                for (c, s, d), cnt in open_slots.items() if cnt > 0
            ]
            if not missing_slots:
                break

            logger.info("Retry round %d for missing slots: %s", round_num, missing_slots)
            try:
                retry_raw = await _fill_slots_batch(
                    client=client,
                    job_title=job_title,
                    job_summary=job_summary,
                    candidate=candidate,
                    slots=missing_slots,
                    exclusions=seen_texts,
                )
            except LLMClientError as err:
                logger.warning("Retry round %d failed: %s", round_num, err)
                notes.append(_friendly_error(err))
                llm_errors.append(err)
                break
            retry_val = validate_question_batch(
                raw_questions=retry_raw,
                open_slots=open_slots,
                exclusions=seen_texts,
            )
            for q in retry_val.valid:
                if dedup_fn(q["question"], seen_texts):
                    warnings.append(f"Retry dropped duplicate question testing {q['skill']}")
                    slot_key = (q.get("competency", "Core"), q["skill"], q["difficulty"])
                    open_slots[slot_key] += 1
                else:
                    kept_questions.append(q)
                    seen_texts.append(q["question"])

            if sum(open_slots.values()) == 0:
                break

    # Record note if any slots remain missing after all retries
    if sum(open_slots.values()) > 0:
        missing_details = [
            f"{c}/{s}/{d} x{cnt}"
            for (c, s, d), cnt in open_slots.items() if cnt > 0
        ]
        notes.append(f"Some questions are missing: {'; '.join(missing_details)}")
        warnings.append(f"Generated {len(kept_questions)} of {total_requested} budgeted questions. Missing: {'; '.join(missing_details)}")

    # 8. Fallback to Demo Plan if Gemini Failed Completely
    if not kept_questions and settings.demo_fallback:
        try:
            demo_plan = copy.deepcopy(load_demo_plan())
            reason = "The AI service is unavailable right now, so a saved demo plan is shown instead of new questions."
            demo_plan["status"] = "partial"          # never "ready": these are not questions for this job
            demo_plan["source"] = "demo_cache"
            demo_plan["is_fallback"] = True
            demo_plan["total_requested"] = total_requested   # real budget, so callers can see the shortfall
            demo_plan["total_questions"] = len(demo_plan.get("questions", []))
            demo_plan["note"] = reason
            demo_plan["notes"] = list(dict.fromkeys([reason] + [n for n in notes if not n.startswith("Some questions are missing")]))
            demo_plan["warnings"] = ["Saved demo plan shown; its skills may not match this job's budget."]
            for dq in demo_plan.get("questions", []):
                dq.setdefault("text", dq.get("question", ""))
            return demo_plan
        except FileNotFoundError:
            pass

    # 9. Align Questions with Metadata (id, rationale, competency, status)
    skill_info_map = {(r["competency"], r["skill"]): (r.get("skill_info", {}), r.get("skill_share", 0.0)) for r in all_rows}

    # Match each question to a budget row
    final_questions: List[Dict[str, Any]] = []
    row_idx = 0
    for q in kept_questions:
        # Assign competency from matching row or skill
        comp = q.get("competency")   # set by the validator from the slot it filled
        if not comp:
            matched_row = next((r for r in all_rows if r["skill"].lower() == q["skill"].lower()), None)
            comp = matched_row["competency"] if matched_row else "Core Competency"
        q["competency"] = comp
        skill_info, share = skill_info_map.get((comp, q["skill"]), ({}, 0.0))

        q_id = f"q_{uuid.uuid4().hex[:10]}"   # schema: unique across ALL plans (q_001 collided between plans)
        row_idx += 1

        final_questions.append({
            "id": q_id,
            "competency": comp,
            "skill": q["skill"],
            "difficulty": q["difficulty"],
            "text": q["question"],          # Matches MongoDB questions item schema ('text')
            "question": q["question"],      # Kept for backward compatibility
            "key_points": q["key_points"],
            "rationale": make_rationale(q, skill_info, share, is_thin_jd),
            "assumed": is_thin_jd,
            "status": "pending",
        })

    # Record warning if fewer questions were generated than budgeted
    if len(final_questions) < total_requested:
        warnings.append(f"Generated {len(final_questions)} of {total_requested} requested questions due to filter/rate limits.")

    is_complete = len(final_questions) >= total_requested
    plan_status = "ready" if is_complete else "partial"
    primary_note = "" if is_complete else f"Only {len(final_questions)} of {total_requested} questions could be generated"
    if not is_complete and llm_errors:
        primary_note += f". {_friendly_error(llm_errors[0])}"
    notes = list(dict.fromkeys(notes))

    response_payload = {
        "status": plan_status,
        "job_id": job.get("id", ""),
        "candidate_id": candidate.get("id", ""),
        "job_title": job_title,
        "candidate_name": candidate.get("name", ""),
        "total_questions": len(final_questions),
        "total_requested": total_requested,
        "settings": {
            "interview_minutes": settings.interview_minutes,
            "difficulty": settings.difficulty_override or "auto",
            "difficulty_mix": budget.get("diff_mix", {}),
        },
        "note": primary_note,
        "notes": notes,
        "coverage": budget.get("allocation", []),
        "budget_table": budget.get("budget_table", ""),
        "questions": final_questions,
        "warnings": warnings,
        "source": "generated",
    }

    # Store in Cache if valid questions generated
    if settings.use_cache and cache_key and final_questions and is_complete:   # never cache partial plans
        cache_store.set(cache_key, response_payload, ttl_seconds=config.CACHE_TTL_SECONDS)

    return response_payload
