
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from .skill_matcher import match_skills
except ImportError:
    try:
        from Backend.services.skill_matcher import match_skills
    except ImportError:
        from skill_matcher import match_skills



BASE_DIR = Path(__file__).resolve().parent.parent
COMPETENCIES_PATH = BASE_DIR / "data" / "competencies.json"

# Factors used to calculate each skill's original weight.
FACTOR_WEIGHTS = {
    "requirement_level": 0.35,
    "frequency": 0.25,
    "position": 0.15,
    "years_requested": 0.15,
    "title_relevance": 0.10,
}

# Configurable information-quality thresholds.
MIN_SKILLS_FOR_INFORMATIVE_JD = 3
MIN_JD_WORDS = 10
SHORT_JD_WORDS = 20

# Fallback skills are assumptions, not confirmed JD requirements.
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
    """Load competency configuration."""
    if not COMPETENCIES_PATH.exists():
        return {"competencies": [], "merge_groups": []}

    with COMPETENCIES_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("competencies.json must contain a JSON object.")

    data.setdefault("competencies", [])
    data.setdefault("merge_groups", [])
    return data


def normalize_text(text: str) -> str:
    """Normalize whitespace."""
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> list[str]:
    """Split text into sentences without splitting common technical names."""
    protected = re.sub(
        r"(?i)(?<!\w)(?:Node\.js|React\.js|Next\.js|Vue\.js|\.NET)",
        lambda match: match.group().replace(".", "\u0001"),
        text,
    )

    pattern = re.compile(r"[^.!?\n]+(?:[.!?]+|$)")
    sentences = []

    for match in pattern.finditer(protected):
        sentence = text[match.start():match.end()].strip()
        if sentence:
            sentences.append(sentence)

    return sentences


def detect_requirement_level(sentence: str) -> tuple[str, float]:
    """Classify requirement strength from a sentence."""
    text = sentence.casefold()

    required_patterns = [
        r"\brequired\b",
        r"\bmust have\b",
        r"\bmandatory\b",
        r"\bessential\b",
        r"\bminimum requirement\b",
        r"\bneed to have\b",
        r"\bmust be proficient\b",
    ]

    preferred_patterns = [
        r"\bpreferred\b",
        r"\bdesired\b",
        r"\bnice to have\b",
        r"\bplus\b",
        r"\bfamiliarity with\b",
        r"\bgood to have\b",
        r"\bwould be an advantage\b",
    ]

    if any(re.search(p, text) for p in required_patterns):
        return "required", 1.0

    if any(re.search(p, text) for p in preferred_patterns):
        return "preferred", 0.5

    return "unspecified", 0.7


def classify_skill_requirement(
    evidence_sentences: list[str],
) -> tuple[str, float]:
    """Classify a skill using all its evidence sentences."""
    classifications = [
        detect_requirement_level(sentence)
        for sentence in evidence_sentences
    ]

    # Required takes precedence over preferred.
    for level, score in classifications:
        if level == "required":
            return level, score

    for level, score in classifications:
        if level == "preferred":
            return level, score

    return "unspecified", 0.7


def detect_years_requested(text: str) -> float:
    """Convert requested experience duration into a scoring signal."""
    text = text.casefold()

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
    if max_years <= 3:
        return 0.5
    if max_years <= 5:
        return 0.75

    return 1.0


def detect_position(sentence: str, full_text: str) -> float:
    """Give more weight to skills appearing earlier in the JD."""
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
    """Normalize mention frequency against the maximum."""
    if maximum <= 0:
        return 0.0

    return round(count / maximum, 3)


def calculate_title_relevance(
    skill_name: str,
    role_title: str,
    competency: str,
) -> float:
    """Estimate a skill's relevance to the role title."""
    if not role_title.strip():
        return 0.5

    title_words = set(
        re.findall(r"[a-zA-Z+#.]+", role_title.casefold())
    )
    skill_words = set(
        re.findall(r"[a-zA-Z+#.]+", skill_name.casefold())
    )
    competency_words = set(
        re.findall(r"[a-zA-Z+#.]+", competency.casefold())
    )

    if skill_words.intersection(title_words):
        return 1.0

    if competency_words.intersection(title_words):
        return 0.8

    return 0.5


def normalize_skill_weights(
    weighted_skills: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Add normalized weights without changing original weights."""
    total = sum(
        max(0.0, float(skill.get("weight", 0.0)))
        for skill in weighted_skills
    )

    for skill in weighted_skills:
        original_weight = max(0.0, float(skill.get("weight", 0.0)))
        skill["normalized_weight"] = (
            round(original_weight / total, 6) if total > 0 else 0.0
        )

    # Correct minor rounding drift.
    if weighted_skills and total > 0:
        normalized_total = sum(
            skill["normalized_weight"] for skill in weighted_skills
        )
        largest = max(
            weighted_skills,
            key=lambda skill: skill["normalized_weight"],
        )
        largest["normalized_weight"] = round(
            largest["normalized_weight"] + (1.0 - normalized_total),
            6,
        )

    return weighted_skills


def build_competency_groups(
    weighted_skills: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Group skills and apply configured competency merges."""
    configuration = load_competencies()
    merge_groups = configuration.get("merge_groups", [])

    present_names = {
        skill["name"].casefold()
        for skill in weighted_skills
    }

    active_merges = []

    for merge_group in merge_groups:
        if not isinstance(merge_group, dict):
            continue

        if not merge_group.get("merge_when_co_required", False):
            continue

        configured_skills = merge_group.get("skills", [])
        present_group_skills = [
            name for name in configured_skills
            if isinstance(name, str) and name.casefold() in present_names
        ]

        if len(present_group_skills) >= 2:
            active_merges.append({
                "name": merge_group.get(
                    "name", "Combined Competency"
                ),
                "skills": {
                    name.casefold() for name in present_group_skills
                },
            })

    groups = defaultdict(list)

    for skill in weighted_skills:
        group_name = skill.get("competency", "Other")
        skill_name = skill.get("name", "").casefold()

        for merge in active_merges:
            if skill_name in merge["skills"]:
                group_name = merge["name"]
                break

        groups[group_name].append(skill)

    result = []

    for competency, skills in sorted(groups.items()):
        result.append({
            "competency": competency,
            "skills": skills,
            "skill_count": len(skills),
            "total_weight": round(
                sum(skill.get("weight", 0.0) for skill in skills), 4
            ),
            "total_normalized_weight": round(
                sum(
                    skill.get("normalized_weight", 0.0)
                    for skill in skills
                ),
                6,
            ),
        })

    return result


def find_fallback_skills(role_title: str) -> list[str]:
    """Return assumed skills for supported role titles."""
    title = role_title.casefold()

    for role, skills in ROLE_FALLBACKS.items():
        if role in title:
            return skills.copy()

    return []


def assess_information_quality(
    text: str,
    weighted_skills: list[dict[str, Any]],
) -> tuple[bool, list[str]]:
    """Flag job descriptions that lack sufficient information."""
    word_count = len(text.split())
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

    if word_count < MIN_JD_WORDS:
        reasons.append("The job description is extremely short.")

    if skill_count < MIN_SKILLS_FOR_INFORMATIVE_JD:
        reasons.append(
            f"Fewer than {MIN_SKILLS_FOR_INFORMATIVE_JD} known skills "
            "were detected."
        )

    if word_count < SHORT_JD_WORDS and not has_requirement_details:
        reasons.append(
            "The description contains little requirement information."
        )

    return bool(reasons), list(dict.fromkeys(reasons))


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
        fallback_skills = find_fallback_skills(role_title)
        warnings = ["The job description is empty."]

        if fallback_skills:
            warnings.append(
                "Fallback skills are assumptions based on the role title, "
                "not skills explicitly detected in the job description."
            )

        return {
            "role_title": role_title,
            "weighted_skills": [],
            "competency_groups": [],
            "low_info": True,
            "assumed_skills": fallback_skills,
            "warnings": warnings,
            "factor_weights": FACTOR_WEIGHTS.copy(),
            "summary": {
                "word_count": 0,
                "detected_skill_count": 0,
                "sentence_count": 0,
                "normalized_weight_sum": 0.0,
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
    experience_score = detect_years_requested(text)
    weighted_skills = []

    for skill_name, mentions in skill_mentions.items():
        competency = mentions[0]["competency"]

        evidence_sentences = list(dict.fromkeys(
            item["sentence"]
            for item in mentions
            if item.get("sentence")
        ))

        requirement_level, requirement_score = (
            classify_skill_requirement(evidence_sentences)
        )

        frequency_score = calculate_frequency_score(
            len(mentions),
            maximum_frequency,
        )

        first_mention = min(mentions, key=lambda item: item["start"])
        evidence = first_mention["sentence"]
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

        weighted_skills.append({
            "name": skill_name,
            "competency": competency,
            "weight": round(final_score, 4),
            "normalized_weight": 0.0,
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
            "all_evidence": evidence_sentences,
        })

    weighted_skills.sort(
        key=lambda item: item["weight"],
        reverse=True,
    )

    normalize_skill_weights(weighted_skills)

    low_info, quality_reasons = assess_information_quality(
        text,
        weighted_skills,
    )

    warnings = quality_reasons.copy()

    if not role_title:
        warnings.append(
            "No role title was supplied; neutral title relevance was used."
        )

    # Remove fallback skills already detected explicitly in the JD.
    detected_names = {
        skill["name"].casefold()
        for skill in weighted_skills
    }

    assumed_skills = [
        skill
        for skill in (
            find_fallback_skills(role_title) if low_info else []
        )
        if skill.casefold() not in detected_names
    ]

    if assumed_skills:
        warnings.append(
            "Fallback skills are assumptions based on the role title, "
            "not skills explicitly detected in the job description."
        )

    competency_groups = build_competency_groups(weighted_skills)

    return {
        "role_title": role_title,
        "weighted_skills": weighted_skills,
        "competency_groups": competency_groups,
        "low_info": low_info,
        "assumed_skills": assumed_skills,
        "warnings": warnings,
        "factor_weights": FACTOR_WEIGHTS.copy(),
        "summary": {
            "word_count": len(text.split()),
            "detected_skill_count": len(weighted_skills),
            "sentence_count": len(sentences),
            "normalized_weight_sum": round(
                sum(
                    skill["normalized_weight"]
                    for skill in weighted_skills
                ),
                6,
            ),
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
        print(
            f"Detected skills: "
            f"{result['summary']['detected_skill_count']}"
        )
        print(
            f"Normalized weight sum: "
            f"{result['summary']['normalized_weight_sum']}"
        )
        print(f"Assumed skills: {result['assumed_skills']}")
        print("Skill weights:")

        for skill in result["weighted_skills"]:
            print(
                f"  {skill['name']}: "
                f"weight={skill['weight']}, "
                f"normalized={skill['normalized_weight']}, "
                f"requirement={skill['requirement_level']}"
            )
