"""Unit tests for services/difficulty/difficulty_service.py."""
import pytest
from services.difficulty.difficulty_service import (
    calculate_difficulty_mix,
    calculate_skill_difficulty_mix,
)


def test_standard_difficulty_mixes_sum_to_100():
    """Verify standard bands produce distributions that sum to 100%."""
    for band in ["beginner", "intermediate", "advanced"]:
        mix = calculate_difficulty_mix(candidate_band=band)
        assert sum(mix.values()) == 100
        assert mix["easy"] >= 0
        assert mix["medium"] >= 0
        assert mix["hard"] >= 0


def test_default_band_for_unknown():
    """Unknown or empty band should fall back to intermediate."""
    mix_default = calculate_difficulty_mix(candidate_band="intermediate")
    mix_unknown = calculate_difficulty_mix(candidate_band="unknown_tier")
    assert mix_unknown == mix_default


def test_seniority_derivation():
    """Derive band correctly from years of experience or seniority string."""
    assert calculate_difficulty_mix(seniority=1)["easy"] == 50  # beginner
    assert calculate_difficulty_mix(seniority=3)["medium"] == 50  # intermediate
    assert calculate_difficulty_mix(seniority=8)["hard"] == 60  # advanced
    assert calculate_difficulty_mix(seniority="Senior Lead")["hard"] == 60


def test_string_overrides():
    """Verify string overrides like 'easy', 'medium', 'hard' set 100%."""
    assert calculate_difficulty_mix(override="easy") == {"easy": 100, "medium": 0, "hard": 0}
    assert calculate_difficulty_mix(override="medium") == {"easy": 0, "medium": 100, "hard": 0}
    assert calculate_difficulty_mix(override="hard") == {"easy": 0, "medium": 0, "hard": 100}


def test_dict_override():
    """Verify custom dict override sums to 100 and applies."""
    custom = {"easy": 25, "medium": 50, "hard": 25}
    assert calculate_difficulty_mix(override=custom) == custom

    with pytest.raises(ValueError):
        calculate_difficulty_mix(override={"easy": 50, "medium": 10})  # sums to 60, invalid


def test_skill_evidence_shift():
    """Strong evidence on important skill shifts harder; gaps shift easier."""
    base = calculate_difficulty_mix(candidate_band="intermediate")  # 20, 50, 30

    # Strong evidence shift harder
    shifted_hard = calculate_skill_difficulty_mix(base, skill_share=0.3, candidate_evidence="strong")
    assert sum(shifted_hard.values()) == 100
    assert shifted_hard["hard"] > base["hard"]
    assert shifted_hard["easy"] < base["easy"]

    # Gap shift easier
    shifted_easy = calculate_skill_difficulty_mix(base, skill_share=0.3, candidate_evidence="gap")
    assert sum(shifted_easy.values()) == 100
    assert shifted_easy["easy"] > base["easy"]
    assert shifted_easy["hard"] < base["hard"]


def test_deterministic_outputs():
    """Identical inputs must produce identical outputs."""
    res1 = calculate_difficulty_mix("beginner", seniority=1)
    res2 = calculate_difficulty_mix("beginner", seniority=1)
    assert res1 == res2
