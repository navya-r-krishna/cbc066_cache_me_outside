"""InterviewIQ - Validation Module

Provides Pydantic models and deterministic validation logic to ensure
generated interview questions conform to strict quality, length, difficulty,
and uniqueness criteria.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field, field_validator

import config
from llm.prompts import LEVEL_CALIBRATION_EXAMPLES


def _normalize_text(s: str) -> str:
    """Normalize text for basic duplicate detection."""
    return re.sub(r"[^\w\s]", "", s.lower()).strip()


def _skill_tokens(s: str) -> Set[str]:
    return set(re.findall(r"[a-z0-9+#.]+", s.lower()))


class ValidatedQuestion(BaseModel):
    """Pydantic model representing a verified generated question."""
    id: Optional[str] = None
    competency: Optional[str] = None
    skill: str
    difficulty: str
    question: str
    key_points: List[str]
    rationale: Optional[str] = None
    assumed: bool = False
    status: str = "pending"

    @field_validator("difficulty")
    @classmethod
    def check_difficulty(cls, v: str) -> str:
        diff = v.strip().lower()
        if diff not in config.DIFFICULTIES:
            raise ValueError(f"Invalid difficulty '{v}'. Must be one of {config.DIFFICULTIES}")
        return diff

    @field_validator("question")
    @classmethod
    def check_question_text(cls, v: str) -> str:
        q = v.strip()
        min_chars = getattr(config, "MIN_QUESTION_CHARS", 25)
        if len(q) < min_chars:
            raise ValueError(
                f"Question is too short ({len(q)} chars). Minimum required is {min_chars} chars."
            )
        max_chars = getattr(config, "MAX_QUESTION_CHARS", 400)
        if len(q) > max_chars:
            raise ValueError(
                f"Question is too long ({len(q)} chars). Maximum is {max_chars}."
            )
        # Reject copies of level calibration examples
        norm_q = _normalize_text(q)
        for ex in LEVEL_CALIBRATION_EXAMPLES.values():
            if norm_q == _normalize_text(ex):
                raise ValueError("Question cannot copy calibration examples.")
        return q

    @field_validator("key_points")
    @classmethod
    def check_key_points(cls, v: List[str]) -> List[str]:
        cleaned = [p.strip() for p in v if p and p.strip()]
        if len(cleaned) < 2:
            raise ValueError("Question must have at least 2 clear expected-answer key points.")
        max_kp_chars = getattr(config, "MAX_KEY_POINT_CHARS", 220)
        for p in cleaned:
            if len(p) > max_kp_chars:
                raise ValueError(f"Key points must be short (max {max_kp_chars} chars each).")
        # Trim to maximum allowed
        max_kps = getattr(config, "MAX_KEY_POINTS", 5)
        return cleaned[:max_kps]


@dataclass
class ValidationResult:
    """Holds the outcome of validating a batch of questions."""
    valid: List[Dict[str, Any]] = field(default_factory=list)
    invalid: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    remaining_slots: Dict[Any, int] = field(default_factory=dict)

    @property
    def is_all_valid(self) -> bool:
        return len(self.invalid) == 0




def _skills_match(a: str, b: str) -> bool:
    """Whole-word match only. 'Python 3' matches 'Python', but 'NoSQL' does NOT match 'SQL'
    and 'JavaScript' does NOT match 'Java' (the old substring check accepted both)."""
    ta, tb = _skill_tokens(a), _skill_tokens(b)
    return bool(ta) and bool(tb) and (ta <= tb or tb <= ta)


def validate_question_batch(
    raw_questions: List[Dict[str, Any]],
    requested_skills: Optional[Set[str]] = None,
    exclusions: Optional[List[str]] = None,
    open_slots: Optional[Dict[Any, int]] = None,
) -> ValidationResult:
    """Performs deterministic validation on a batch of generated questions.

    Args:
        raw_questions: List of question dicts from Gemini
        requested_skills: Optional set of allowed skill names
        exclusions: Optional list of question texts to avoid repeating
        open_slots: Optional mutable dictionary/Counter mapping slot keys
                    (competency, skill, difficulty) or (skill, difficulty) to remaining counts.

    Returns:
        ValidationResult with separated valid and invalid questions.
    """
    result = ValidationResult()
    seen_texts: Set[str] = set()

    # Pre-populate seen texts with normalized exclusions
    if exclusions:
        for ex in exclusions:
            seen_texts.add(_normalize_text(ex))

    req_skills_lower = {s.lower() for s in requested_skills} if requested_skills else None

    for idx, q_dict in enumerate(raw_questions):
        try:
            # 1. Pydantic schema validation
            model = ValidatedQuestion.model_validate(q_dict)
            q_clean = model.model_dump()

            # 2. Check open slots if provided (exact skill + difficulty matching)
            matched_slot_key = None
            fuzzy_slot_key = None
            if open_slots is not None:
                for slot_key, remaining in open_slots.items():
                    if remaining <= 0:
                        continue
                    slot_skill = slot_key[1] if len(slot_key) == 3 else slot_key[0]
                    slot_diff = slot_key[2] if len(slot_key) == 3 else slot_key[1]

                    if slot_diff.lower() != model.difficulty.lower():
                        continue
                    if " ".join(slot_skill.lower().split()) == " ".join(model.skill.lower().split()):
                        matched_slot_key = slot_key      # exact match always wins
                        break
                    if fuzzy_slot_key is None and _skills_match(slot_skill, model.skill):
                        fuzzy_slot_key = slot_key
                matched_slot_key = matched_slot_key or fuzzy_slot_key

                if not matched_slot_key:
                    err = (
                        f"Question #{idx+1} for skill '{model.skill}' ({model.difficulty}) "
                        f"has no open slot matching this exact skill and difficulty."
                    )
                    result.invalid.append(q_dict)
                    result.errors.append(err)
                    continue

            # 3. Check requested skills filter if open_slots was not passed
            elif req_skills_lower and model.skill.lower() not in req_skills_lower:
                matching = [s for s in req_skills_lower if _skills_match(s, model.skill)]
                if not matching:
                    err = f"Question #{idx+1} tests unexpected skill '{model.skill}'"
                    result.invalid.append(q_dict)
                    result.errors.append(err)
                    continue

            # 4. Check for duplicates within this batch or exclusions
            norm_q = _normalize_text(model.question)
            if norm_q in seen_texts:
                err = f"Question #{idx+1} is duplicate or too similar to an existing question"
                result.invalid.append(q_dict)
                result.errors.append(err)
                continue

            # Successfully claimed slot and passed all validations
            if matched_slot_key is not None and open_slots is not None:
                open_slots[matched_slot_key] -= 1
                # Store the budget's own skill name, so a later "refund" hits the same slot key.
                q_clean["skill"] = matched_slot_key[1] if len(matched_slot_key) == 3 else matched_slot_key[0]
                if len(matched_slot_key) == 3:
                    q_clean["competency"] = matched_slot_key[0]

            seen_texts.add(norm_q)
            result.valid.append(q_clean)

        except Exception as e:
            err = f"Question #{idx+1} failed validation: {e}"
            result.invalid.append(q_dict)
            result.errors.append(err)

    if open_slots is not None:
        result.remaining_slots = {k: v for k, v in open_slots.items() if v > 0}

    return result
