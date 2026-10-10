
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from .skill_matcher import match_skills
except ImportError:
    from skill_matcher import match_skills


BASE_DIR = Path(__file__).resolve().parent.parent
COMPETENCIES_PATH = BASE_DIR / "data" / "competencies.json"

FACTOR_WEIGHTS = {
    "requirement_level": 0.35,
    "frequency": 0.25,
    "position": 0.15,
    "years_requested": 0.15,
    "title_relevance": 0.10,
}

ROLE_FALLBACKS = {
    "data analyst": [
        "Python", "SQL", "Pandas", "Excel", "Data Visualization"
    ],
    "backend developer": [
        "Python", "REST APIs", "SQL", "Authentication"
    ],
    "software developer": [
        "Python", "OOP", "Git", "Testing"
    ],
    "frontend developer": [
        "HTML", "CSS", "JavaScript", "React"
    ],
}


def load_competencies() -> dict[str, Any]:
    """Load competency configuration when available."""

    if not COMPETENCIES_PATH.exists():
        return {"competencies": [], "merge_groups": []}

    with COMPETENCIES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_text(text: str) -> str:
    """Normalize whitespace."""

    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> list[str]:
    """Split text while protecting dots in technical names."""

    protected = re.sub(
        r"(?i)(?<!\w)(?:Node\.js|React\.js|Next\.js|Vue\.js|\.NET)",
        lambda match: match.group().replace(".", "\u0001"),
        text,
    )

    pattern = re.compile(r"[^.!?\n]+(?:[.!?]+|$)")
    sentences = []

    for match in pattern.finditer(protected):
        start, end = match.span()
        sentence = text[start:end].strip()

        if sentence:
            sentences.append(sentence)

    return sentences


def detect_requirement_level(sentence: str) -> tuple[str, float]:
    """Classify the strength of a skill requirement."""

    text = sentence.lower()

    required_patterns = [
        r"\brequired\b",
        r"\bmust have\b",
        r"\bmandatory\b",
        r"\bessential\b",
        r"\bminimum requirement\b",
        r"\bneed to have\b",
    ]

    preferred_patterns = [
        r"\bpreferred\b",
        r"\bdesired\b",
        r"\bnice to have\b",
        r"\bplus\b",
        r"\bfamiliarity with\b",
        r"\bgood to have\b",
    ]

    if any(re.search(pattern, text) for pattern in required_patterns):
        return "required", 1.0

    if any(re.search(pattern, text) for pattern in preferred_patterns):
        return "preferred", 0.5

    return "unspecified", 0.7


def detect_years_requested(text: str) -> float:
    """Score the experience requirement across the complete job description."""

    text = text.lower()

    patterns = [
        r"\b(\d+)\s*\+?\s*years?\b",
        r"\bminimum of\s+(\d+)\s*years?\b",
        r"\bat least\s+(\d+)\s*years?\b",
    ]

    years = []

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            years.append(int(match.group(1)))

    if not years:
        return 0.5

    max_years = max(years)

    if max_years <= 1:
        return 0.3
    elif max_years <= 3:
        return 0.5
    elif max_years <= 5:
        return 0.75

    return 1.0


def detect_position(sentence: str, full_text: str) -> float:
    """Score skills mentioned earlier in the description."""

    sentences = split_sentences(full_text)

    if not sentences:
        return 0.5

    try:
        index = sentences.index(sentence)
    except ValueError:
        return 0.5

    if len(sentences) == 1:
        return 1.0

    relative_position = index / (len(sentences) - 1)

    return round(1.0 - (0.5 * relative_position), 3)


def calculate_frequency_score(count: int, maximum: int) -> float:
    """Normalize a skill's mention frequency."""

    if maximum <= 0:
        return 0.0

    return round(count / maximum, 3)


def calculate_title_relevance(
    skill_name: str,
    role_title: str,
    competency: str,
) -> float:
    """Estimate skill relevance to the job title."""

    if not role_title.strip():
        return 0.5

    title_words = set(
        re.findall(r"[a-zA-Z+#.]+", role_title.lower())
    )
    skill_words = set(
        re.findall(r"[a-zA-Z+#.]+", skill_name.lower())
    )
    competency_words = set(
        re.findall(r"[a-zA-Z+#.]+", competency.lower())
    )

    if skill_words.intersection(title_words):
        return 1.0

    if competency_words.intersection(title_words):
        return 0.8

    return 0.5


def build_competency_groups(
    weighted_skills: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Group skills by competency."""

    groups = defaultdict(list)

    for skill in weighted_skills:
        groups[skill["competency"]].append(skill)

    return [
        {
            "competency": competency,
            "skills": skills,
            "skill_count": len(skills),
        }
        for competency, skills in sorted(groups.items())
    ]


def find_fallback_skills(role_title: str) -> list[str]:
    """Return assumed skills for supported job titles."""

    title = role_title.lower()

    for role, skills in ROLE_FALLBACKS.items():
        if role in title:
            return skills.copy()

    return []


def assess_information_quality(
    text: str,
    weighted_skills: list[dict[str, Any]],
) -> tuple[bool, list[str]]:
    """
    Assess information quality using length, detected skills,
    and the availability of meaningful requirement details.
    """

    words = text.split()
    word_count = len(words)
    skill_count = len(weighted_skills)

    requirement_patterns = [
        r"\brequired\b",
        r"\bmust have\b",
        r"\bmandatory\b",
        r"\bessential\b",
        r"\bpreferred\b",
        r"\bdesired\b",
        r"\bexperience\b",
        r"\bresponsibilities\b",
        r"\bqualifications\b",
        r"\bskills\b",
        r"\byears?\b",
    ]

    has_requirement_details = any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in requirement_patterns
    )

    reasons = []

    # Very short descriptions are insufficient regardless of skill count.
    if word_count < 10:
        reasons.append("The job description is extremely short.")

    # Few detected skills alone are not enough to flag a description.
    # The description must also lack useful requirement details or be short.
    if skill_count < 2 and (
        word_count < 30 or not has_requirement_details
    ):
        reasons.append(
            "Fewer than two known skills were detected."
        )

    # Descriptions with limited length and no meaningful requirements
    # should be flagged even if a skill happens to be detected.
    if word_count < 20 and not has_requirement_details:
        reasons.append(
            "The description contains little requirement information."
        )

    return bool(reasons), reasons


def analyze_job(
    job_description: str,
    role_title: str = "",
) -> dict[str, Any]:
    """Analyze a job description and return weighted skill information."""

    if not isinstance(job_description, str):
        raise TypeError("job_description must be a string.")

    if not isinstance(role_title, str):
        raise TypeError("role_title must be a string.")

    text = normalize_text(job_description)
    role_title = role_title.strip()

    if not text:
        return {
            "role_title": role_title,
            "weighted_skills": [],
            "competency_groups": [],
            "low_info": True,
            "assumed_skills": find_fallback_skills(role_title),
            "warnings": ["The job description is empty."],
            "factor_weights": FACTOR_WEIGHTS.copy(),
            "summary": {
                "word_count": 0,
                "detected_skill_count": 0,
                "sentence_count": 0,
            },
        }

    sentences = split_sentences(text)
    matches = match_skills(text)

    skill_mentions = defaultdict(list)

    for match in matches:
        skill_mentions[match["name"]].append(match)

    mention_counts = {
        name: len(items)
        for name, items in skill_mentions.items()
    }

    maximum_frequency = max(mention_counts.values(), default=0)

    # Experience requirements are extracted from the complete description.
    experience_score = detect_years_requested(text)

    weighted_skills = []

    for skill_name, mentions in skill_mentions.items():
        first_mention = mentions[0]
        evidence = first_mention["sentence"]
        competency = first_mention["competency"]

        requirement_level, requirement_score = (
            detect_requirement_level(evidence)
        )

        frequency_score = calculate_frequency_score(
            len(mentions),
            maximum_frequency,
        )

        position_score = detect_position(evidence, text)

        title_score = calculate_title_relevance(
            skill_name,
            role_title,
            competency,
        )

        final_score = (
            requirement_score * FACTOR_WEIGHTS["requirement_level"]
            + frequency_score * FACTOR_WEIGHTS["frequency"]
            + position_score * FACTOR_WEIGHTS["position"]
            + experience_score * FACTOR_WEIGHTS["years_requested"]
            + title_score * FACTOR_WEIGHTS["title_relevance"]
        )

        weighted_skills.append(
            {
                "name": skill_name,
                "competency": competency,
                "weight": round(final_score, 4),
                "requirement_level": requirement_level,
                "mention_count": len(mentions),
                "signals": {
                    "requirement_level": round(requirement_score, 3),
                    "frequency": frequency_score,
                    "position": position_score,
                    "years_requested": round(experience_score, 3),
                    "title_relevance": round(title_score, 3),
                },
                "evidence": evidence,
                "all_evidence": list(
                    dict.fromkeys(
                        item["sentence"] for item in mentions
                    )
                ),
            }
        )

    weighted_skills.sort(
        key=lambda item: item["weight"],
        reverse=True,
    )

    low_info, quality_reasons = assess_information_quality(
        text,
        weighted_skills,
    )

    warnings = quality_reasons.copy()

    if not role_title:
        warnings.append(
            "No role title was supplied; neutral title relevance was used."
        )

    assumed_skills = (
        find_fallback_skills(role_title) if low_info else []
    )

    return {
        "role_title": role_title,
        "weighted_skills": weighted_skills,
        "competency_groups": build_competency_groups(weighted_skills),
        "low_info": low_info,
        "assumed_skills": assumed_skills,
        "warnings": warnings,
        "factor_weights": FACTOR_WEIGHTS.copy(),
        "summary": {
            "word_count": len(text.split()),
            "detected_skill_count": len(weighted_skills),
            "sentence_count": len(sentences),
        },
    }


if __name__ == "__main__":
    test_cases = [
        {
            "title": "Data Analyst",
            "description": (
                "Python and SQL skills are required. "
                "The candidate must have at least 5 years "
                "of professional experience."
            ),
        },
        {
            "title": "Data Analyst",
            "description": (
                "We are looking for a Data Analyst to analyze business "
                "data, create dashboards, prepare reports, identify trends, "
                "collaborate with teams, and communicate insights. "
                "Strong Python and SQL skills are required. "
                "Experience with Pandas and NumPy is preferred."
            ),
        },
        {
            "title": "Backend Developer",
            "description": "Python developer.",
        },
    ]

    for test in test_cases:
        result = analyze_job(
            job_description=test["description"],
            role_title=test["title"],
        )

        print("\n" + "=" * 60)
        print(f"Role: {result['role_title']}")
        print(f"Low information: {result['low_info']}")
        print(f"Warnings: {result['warnings']}")
        print(f"Detected skills: {result['summary']['detected_skill_count']}")
        print(f"Assumed skills: {result['assumed_skills']}")
