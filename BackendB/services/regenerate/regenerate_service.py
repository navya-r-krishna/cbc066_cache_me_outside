"""InterviewIQ - Question Regeneration Service

Allows interviewers to swap or adjust an existing interview question with
an alternative targeting the same skill and difficulty, taking interviewer
hints into account while avoiding duplicates and previously asked questions.
"""
from __future__ import annotations

import copy
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional

import config
from llm.client import GeminiClient, LLMClientError
from llm.prompts import SingleQuestionResponse, build_regeneration_prompt
from services.question_gen.generator import default_dedup_checker
from utils.validators import validate_question_batch

logger = logging.getLogger("interviewiq.regenerate")


def _qtext(q: Dict[str, Any]) -> str:
    """Questions stored in MongoDB use 'text'; older B output used 'question'. Accept both."""
    return (q.get("text") or q.get("question") or "").strip()


class RegenerationError(Exception):
    """Raised when question regeneration fails all retry attempts."""
    pass


async def regenerate_question(
    question: Dict[str, Any],
    plan: Dict[str, Any],
    hint: Optional[str] = None,
    *,
    client: Optional[GeminiClient] = None,
    dedup: Optional[Callable[[str, List[str]], bool]] = None,
    feedback_logger: Optional[Callable[[Dict[str, Any]], None]] = None,
    history: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Regenerates a single question with interviewer hint and duplicate prevention.

    Args:
        question: The target question dictionary being replaced.
        plan: The current interview plan containing role context and other questions.
        hint: Optional interviewer guidance (e.g., 'more practical', 'focus on async').
        client: GeminiClient instance.
        dedup: Optional duplicate detection adapter from Backend C.
        feedback_logger: Optional callback to record replacement metadata for Backend C.
        history: Excluded question texts candidate has already answered.

    Returns:
        The replacement question dictionary. If all attempts fail, returns the original question.
    """
    client = client or GeminiClient()
    dedup_fn = dedup or default_dedup_checker

    job_title = plan.get("job_title") or plan.get("role") or "Technical Candidate"
    competency = question.get("competency", "Core Competency")
    skill = question.get("skill", "General Skill")
    difficulty = question.get("difficulty", "medium")
    orig_text = _qtext(question)
    orig_id = question.get("id", "q_000")

    # Build exclusion list: all active questions in plan + original + history
    existing_plan_questions = [_qtext(q) for q in plan.get("questions", [])]   # includes rejected ones
    rejected_questions = plan.get("rejected_questions", [])
    exclusions: List[str] = list(
        dict.fromkeys(
            [q for q in (existing_plan_questions + rejected_questions + list(history or [])) if q]
        )
    )

    clean_hint = (hint or "").strip()[:200] if hint else None
    last_error: Optional[str] = None

    for attempt in range(1, config.MAX_REGEN_ATTEMPTS + 1):
        prompt = build_regeneration_prompt(
            job_title=job_title,
            competency=competency,
            skill=skill,
            difficulty=difficulty,
            original_question=orig_text,
            hint=clean_hint,
            exclusions=exclusions,
        )

        try:
            resp = await client.generate_structured(prompt, SingleQuestionResponse, purpose="regenerate_question")
            candidate_dict = resp.model_dump()

            # Ensure skill and difficulty match the target requirement
            candidate_dict["skill"] = skill
            candidate_dict["difficulty"] = difficulty
            candidate_dict["competency"] = competency

            # Validate using standard validator
            val_result = validate_question_batch([candidate_dict], requested_skills={skill}, exclusions=exclusions)
            if not val_result.is_all_valid:
                last_error = "; ".join(val_result.errors)
                logger.warning("Regeneration attempt %d failed validation: %s", attempt, last_error)
                continue

            clean_q = val_result.valid[0]

            # Check duplicate detection adapter
            if dedup_fn(clean_q["question"], exclusions):
                last_error = "Duplicate of existing question"
                exclusions.append(clean_q["question"])
                logger.warning("Regeneration attempt %d flagged as duplicate", attempt)
                continue

            # Successfully validated replacement
            new_id = f"reg_{uuid.uuid4().hex[:6]}"
            new_question = {
                "id": new_id,
                "competency": competency,
                "skill": skill,
                "difficulty": difficulty,
                "text": clean_q["question"],          # Matches MongoDB questions item schema ('text')
                "question": clean_q["question"],      # Kept for backward compatibility
                "key_points": clean_q["key_points"],
                "rationale": question.get("rationale") or f"Tests {skill} under {competency} ({difficulty}). Regenerated replacement.",
                "assumed": question.get("assumed", False),
                "status": "pending",
                "replaced_question_id": orig_id,
            }

            # Log feedback for Backend C
            if feedback_logger:
                feedback_data = {
                    "action": "regenerated",
                    "plan_id": plan.get("id", ""),
                    "question_id": orig_id,
                    "hint": clean_hint,
                    "question_text": orig_text,            # the REPLACED question: it joins the do-not-repeat list
                    "new_question_text": clean_q["question"],
                    "original_question_id": orig_id,
                    "new_question_id": new_id,
                    "skill": skill,
                    "difficulty": difficulty,
                }
                try:
                    feedback_logger(feedback_data)
                except Exception as ex:
                    logger.warning("Feedback logger error: %s", ex)

            return new_question

        except LLMClientError as e:
            last_error = str(e)
            logger.warning("Regeneration LLM call failed on attempt %d: %s", attempt, e)
            break   # the client already retried; looping again just burns quota

    # Fail loudly: the route should keep the original question and tell the user, not report success.
    logger.error("Regeneration failed (%s). Original question left unchanged.", last_error)
    raise RegenerationError("Could not generate a replacement question right now. The original question was kept.")
