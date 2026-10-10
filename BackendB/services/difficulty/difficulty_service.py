"""InterviewIQ - Difficulty Distribution Service

Calculates deterministic easy/medium/hard percentage distributions based on
candidate experience, seniority, interviewer overrides, and skill evidence.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Union
import config


def _normalize_band(band: Optional[str], seniority: Optional[Union[int, float, str]] = None) -> str:
    """Resolve candidate seniority band deterministically."""
    if band:
        b = band.strip().lower()
        if b in config.DEFAULT_DIFFICULTY_MIX:
            return b
        if "junior" in b or "entry" in b or "intern" in b or "fresher" in b:
            return "beginner"
        if "senior" in b or "lead" in b or "principal" in b or "staff" in b:
            return "advanced"
        if "mid" in b or "intermediate" in b:
            return "intermediate"

    # Derive from years of experience if provided
    if seniority is not None:
        try:
            years = float(seniority)
            if years < 2.0:
                return "beginner"
            elif years < 5.0:
                return "intermediate"
            else:
                return "advanced"
        except (ValueError, TypeError):
            s = str(seniority).lower()
            if "junior" in s or "entry" in s:
                return "beginner"
            if "senior" in s or "lead" in s:
                return "advanced"

    return config.DEFAULT_CANDIDATE_BAND


def calculate_difficulty_mix(
    candidate_band: Optional[str] = None,
    seniority: Optional[Union[int, float, str]] = None,
    override: Optional[Union[str, Dict[str, int]]] = None,
) -> Dict[str, int]:
    """Computes difficulty distribution (easy, medium, hard percentages) summing to 100.

    Args:
        candidate_band: 'beginner', 'intermediate', or 'advanced'
        seniority: Years of experience or seniority level string
        override: Optional override like 'easy', 'medium', 'hard', 'automatic',
                  or a dict like {'easy': 20, 'medium': 50, 'hard': 30}.

    Returns:
        Dict with keys 'easy', 'medium', 'hard' whose values sum to 100.
    """
    # 1. Handle explicit overrides
    if override and override != "automatic":
        if isinstance(override, str):
            ov = override.strip().lower()
            if ov == "easy":
                return {"easy": 100, "medium": 0, "hard": 0}
            elif ov == "medium":
                return {"easy": 0, "medium": 100, "hard": 0}
            elif ov == "hard":
                return {"easy": 0, "medium": 0, "hard": 100}
            elif ov in config.DEFAULT_DIFFICULTY_MIX:
                return dict(config.DEFAULT_DIFFICULTY_MIX[ov])
            else:
                raise ValueError(f"Unknown difficulty override: '{override}'")

        elif isinstance(override, dict):
            keys = set(override.keys())
            if not keys.issubset(set(config.DIFFICULTIES)):
                raise ValueError(f"Override dict must only contain 'easy', 'medium', 'hard', got {keys}")
            mix = {d: int(override.get(d, 0)) for d in config.DIFFICULTIES}
            total = sum(mix.values())
            if total != 100:
                raise ValueError(f"Difficulty override values must sum to 100, got {total}")
            return mix

    # 2. Map candidate to standard band
    band = _normalize_band(candidate_band, seniority)
    base = config.DEFAULT_DIFFICULTY_MIX.get(band, config.DEFAULT_DIFFICULTY_MIX[config.DEFAULT_CANDIDATE_BAND])
    return dict(base)


def calculate_skill_difficulty_mix(
    base_mix: Dict[str, int],
    skill_share: float = 0.0,
    candidate_evidence: Optional[Union[str, bool]] = None,
    shift_points: int = config.SKILL_SHIFT_POINTS,
) -> Dict[str, int]:
    """Adjusts difficulty mix per skill based on candidate evidence and weighting.

    - Strong evidence or heavily weighted skills shift harder.
    - Missing evidence or gaps shift easier.
    - The resulting percentages are guaranteed to sum to 100.
    """
    mix = dict(base_mix)

    # Normalize evidence string/boolean
    has_strong_evidence = False
    has_gap_or_limited = False

    if isinstance(candidate_evidence, bool):
        has_strong_evidence = candidate_evidence
        has_gap_or_limited = not candidate_evidence
    elif isinstance(candidate_evidence, str):
        ev = candidate_evidence.strip().lower()
        if ev in ("strong", "expert", "high", "good", "verified"):
            has_strong_evidence = True
        elif ev in ("gap", "limited", "none", "weak", "missing"):
            has_gap_or_limited = True

    # Shift harder if strong evidence and important skill
    if has_strong_evidence and (skill_share >= 0.15 or candidate_evidence == "strong"):
        # Shift points from easy -> hard (or medium -> hard)
        transfer = min(mix["easy"], shift_points)
        mix["easy"] -= transfer
        mix["hard"] += transfer

    # Shift easier if known gap
    elif has_gap_or_limited:
        # Shift points from hard -> easy (or medium -> easy)
        transfer = min(mix["hard"], shift_points)
        mix["hard"] -= transfer
        mix["easy"] += transfer

    # Invariant: must sum to 100
    total = sum(mix.values())
    if total != 100:
        diff = 100 - total
        mix["medium"] += diff

    return mix
