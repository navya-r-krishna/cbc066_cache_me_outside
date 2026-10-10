
from typing import Any
import re

try:
    from .resume_parser import parse_resume_text, parse_resume_pdf
except ImportError:
    from resume_parser import parse_resume_text, parse_resume_pdf


FACTOR_WEIGHTS = {
    "skills": 0.40,
    "experience": 0.30,
    "role_relevance": 0.20,
    "academics": 0.10,
}

INTERNSHIP_CREDIT = 0.50


def build_candidate_profile(
    resume_text: str | None = None,
    resume_pdf_path: str | None = None,
) -> dict[str, Any]:
    """Build a structured candidate profile from a resume."""

    if bool(resume_text) == bool(resume_pdf_path):
        raise ValueError(
            "Provide exactly one of resume_text or resume_pdf_path."
        )

    if resume_text is not None:
        parsed = parse_resume_text(
            resume_text,
            redact_personal_info=True,
        )
    else:
        parsed = parse_resume_pdf(
            resume_pdf_path,
            redact_personal_info=True,
        )

    skills = parsed.get("skills", [])
    sections = parsed.get("sections", {})

    skill_names = list(
        dict.fromkeys(
            skill["name"]
            for skill in skills
            if skill.get("name")
        )
    )

    summary_parts = [
        sections.get(key, "")
        for key in ("summary", "professional_summary", "profile")
        if sections.get(key)
    ]

    return {
        "skills": skill_names,
        "skill_details": skills,
        "skill_count": len(skill_names),
        "competencies": sorted({
            skill["competency"]
            for skill in skills
            if skill.get("competency")
        }),
        "professional_experience_months": parsed.get(
            "professional_experience_months_estimated", 0
        ),
        "professional_experience_years": parsed.get(
            "professional_experience_years_estimated", 0.0
        ),
        "internship_experience_months": parsed.get(
            "internship_experience_months_estimated", 0
        ),
        "education": parsed.get("education", []),
        "experience_entries": parsed.get("experience_entries", []),
        "resume_summary": "\n".join(summary_parts),
        "candidate_type": parsed.get(
            "candidate_type",
            "fresher_or_experience_not_detected",
        ),
        "pii_redacted": parsed.get("pii_redacted", False),
        "warnings": parsed.get("warnings", []),
    }


def extract_requested_years(
    job_description: str | None,
) -> float | None:
    """Extract an explicit minimum experience requirement."""

    if not job_description:
        return None

    text = job_description.casefold()

    patterns = [
        r"(?:at least|minimum of|min\.?)\s+"
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)"
        r"\s+(?:of\s+)?experience",

        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)"
        r"\s+(?:of\s+)?experience\s+"
        r"(?:is\s+)?(?:required|minimum)",

        r"experience\s+(?:of\s+)?"
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return float(match.group(1))

    return None


def normalize_role_terms(text: str) -> set[str]:
    """Extract meaningful words for basic role-relevance comparison."""

    ignored = {
        "and", "the", "for", "with", "from", "that",
        "this", "have", "has", "had", "our", "your",
        "senior", "junior", "associate", "intern",
        "lead", "principal", "expert", "years",
        "year", "experience", "work", "working",
    }

    return {
        word
        for word in re.findall(r"[a-z0-9+#.]+", text.casefold())
        if len(word) > 1 and word not in ignored
    }


def calculate_role_relevance(
    candidate_profile: dict[str, Any],
    role_title: str,
) -> float | None:
    """Estimate role relevance from summary and experience evidence."""

    if not role_title.strip():
        return None

    role_terms = normalize_role_terms(role_title)

    if not role_terms:
        return None

    evidence_parts = [candidate_profile.get("resume_summary", "")]

    for entry in candidate_profile.get("experience_entries", []):
        if isinstance(entry, dict):
            evidence_parts.append(entry.get("text", ""))

    evidence_text = " ".join(
        part for part in evidence_parts if isinstance(part, str)
    ).strip()

    if not evidence_text:
        return None

    evidence_terms = normalize_role_terms(evidence_text)

    if not evidence_terms:
        return None

    overlap = len(role_terms & evidence_terms) / len(role_terms)

    return round(overlap * 100, 2)


def calculate_relevant_internship_months(
    candidate_profile: dict[str, Any],
    role_title: str,
) -> int:
    """Estimate duration of internships related to the target role."""

    role_terms = normalize_role_terms(role_title)

    if not role_terms:
        return 0

    relevant_ranges = []

    for entry in candidate_profile.get("experience_entries", []):
        if not isinstance(entry, dict):
            continue

        if entry.get("type") != "internship":
            continue

        entry_text = entry.get("text", "")
        entry_terms = normalize_role_terms(entry_text)

        # Require at least one meaningful role-term overlap.
        if not role_terms.intersection(entry_terms):
            continue

        for date_range in entry.get("date_ranges", []):
            try:
                start = date_range["start"]
                end = date_range["end"]

                start_year = int(start["year"])
                start_month = int(start["month"])
                end_year = int(end["year"])
                end_month = int(end["month"])

                if not (
                    1 <= start_month <= 12
                    and 1 <= end_month <= 12
                ):
                    continue

                start_index = start_year * 12 + start_month - 1
                end_index = end_year * 12 + end_month

                if end_index > start_index:
                    relevant_ranges.append((start_index, end_index))

            except (KeyError, TypeError, ValueError):
                continue

    if not relevant_ranges:
        return 0

    # Merge overlapping relevant internship periods to avoid double counting.
    relevant_ranges.sort()
    total_months = 0
    current_start, current_end = relevant_ranges[0]

    for start, end in relevant_ranges[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            total_months += current_end - current_start
            current_start, current_end = start, end

    return total_months + current_end - current_start


def calculate_academic_score(
    candidate_profile: dict[str, Any],
) -> float | None:
    """
    Academic score is unavailable until grades and job requirements
    can be evaluated reliably.
    """

    # An education entry alone does not establish academic performance
    # or whether a qualification satisfies a particular job requirement.
    return None


def compare_candidate_to_job(
    candidate_profile: dict[str, Any],
    job_analysis: dict[str, Any],
    job_description: str | None = None,
) -> dict[str, Any]:
    """Compare skills and calculate a transparent provisional score."""

    candidate_skills = {
        name.casefold()
        for name in candidate_profile.get("skills", [])
    }

    weighted_skills = job_analysis.get("weighted_skills", [])
    matched_skills = []
    missing_skills = []

    for requirement in weighted_skills:
        name = requirement.get("name", "")

        if not name:
            continue

        item = {
            "name": name,
            "weight": requirement.get("weight", 0.0),
            "competency": requirement.get("competency", "Other"),
            "evidence": requirement.get("evidence", ""),
        }

        if name.casefold() in candidate_skills:
            matched_skills.append(item)
        else:
            missing_skills.append(item)

    total_weight = sum(
        item.get("weight", 0.0)
        for item in weighted_skills
        if item.get("name")
    )

    matched_weight = sum(
        item["weight"] for item in matched_skills
    )

    skill_coverage = (
        round(matched_weight / total_weight * 100, 2)
        if total_weight > 0
        else None
    )

    role_title = job_analysis.get("role_title", "")
    requested_years = extract_requested_years(job_description)

    professional_months = max(
        0,
        int(candidate_profile.get("professional_experience_months", 0) or 0),
    )

    relevant_internship_months = calculate_relevant_internship_months(
        candidate_profile,
        role_title,
    )

    equivalent_experience_months = (
        professional_months
        + relevant_internship_months * INTERNSHIP_CREDIT
    )

    experience_score = None

    if requested_years is not None and requested_years > 0:
        required_months = requested_years * 12

        experience_score = round(
            min(equivalent_experience_months / required_months, 1.0)
            * 100,
            2,
        )

    role_score = calculate_role_relevance(
        candidate_profile,
        role_title,
    )

    academic_score = calculate_academic_score(candidate_profile)

    factor_scores = {
        "skills": skill_coverage,
        "experience": experience_score,
        "role_relevance": role_score,
        "academics": academic_score,
    }

    available_factors = {
        name: score
        for name, score in factor_scores.items()
        if score is not None
    }

    available_weight = sum(
        FACTOR_WEIGHTS[name]
        for name in available_factors
    )

    overall_score = None

    if available_weight > 0:
        overall_score = round(
            sum(
                score * FACTOR_WEIGHTS[name]
                for name, score in available_factors.items()
            ) / available_weight,
            2,
        )

    unavailable_factors = [
        name
        for name, score in factor_scores.items()
        if score is None
    ]

    if overall_score is None:
        candidate_band = "insufficient_data"
    elif overall_score >= 75:
        candidate_band = "strong_match"
    elif overall_score >= 50:
        candidate_band = "moderate_match"
    else:
        candidate_band = "developing_match"

    warnings = [
        "Detected skills do not prove proficiency.",
        "The overall score is a heuristic, not a validated hiring prediction.",
        "Available factors are reweighted when other factors cannot be assessed.",
        (
            "Relevant internship months receive 50% credit relative to "
            "professional experience for the experience score."
        ),
    ]

    if requested_years is None:
        warnings.append(
            "Experience score is unavailable because an explicit "
            "experience requirement was not extracted."
        )

    if role_score is None:
        warnings.append(
            "Role relevance could not be estimated from available "
            "summary or experience evidence."
        )

    if academic_score is None:
        warnings.append(
            "Academic score is unavailable because grades and job-specific "
            "qualification requirements are not assessed."
        )

    if unavailable_factors:
        warnings.append(
            "Unavailable scoring factors: "
            + ", ".join(unavailable_factors)
            + ". The overall score is provisional."
        )

    return {
        # Existing API fields are preserved.
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "strengths": [
            item["name"] for item in matched_skills
        ],
        "gaps": [
            {
                "name": item["name"],
                "weight": item["weight"],
                "competency": item["competency"],
            }
            for item in missing_skills
        ],
        "matched_skill_count": len(matched_skills),
        "missing_skill_count": len(missing_skills),
        "skill_coverage_percentage": (
            skill_coverage if skill_coverage is not None else 0.0
        ),
        "low_info": job_analysis.get("low_info", False),
        "warnings": warnings,

        # New scoring fields.
        "factor_scores": factor_scores,
        "factor_weights": FACTOR_WEIGHTS.copy(),
        "overall_score": overall_score,
        "candidate_band": candidate_band,
        "score_is_provisional": bool(unavailable_factors),
        "unavailable_factors": unavailable_factors,
        "experience_breakdown": {
            "professional_months": professional_months,
            "relevant_internship_months": relevant_internship_months,
            "internship_credit": INTERNSHIP_CREDIT,
            "equivalent_experience_months": round(
                equivalent_experience_months, 2
            ),
            "requested_years": requested_years,
        },
    }


if __name__ == "__main__":
    sample_resume = """
    PROFESSIONAL SUMMARY
    BCA student interested in data analysis with Python and SQL.

    TECHNICAL SKILLS
    Python, SQL, Pandas, Machine Learning

    INTERNSHIPS
    Data Analyst Intern
    Example Company
    Jan 2025 - Jun 2025

    EDUCATION
    Bachelor of Computer Applications
    2023 - 2026
    """

    sample_job_description = """
    Data Analyst

    Required skills include Python, SQL, Pandas, and Excel.
    Machine Learning and Data Visualization are preferred.
    The candidate must have at least 2 years of experience.
    Strong communication skills are required.
    """

    candidate = build_candidate_profile(resume_text=sample_resume)

    try:
        from .skill_analysis import analyze_job
    except ImportError:
        from skill_analysis import analyze_job

    job = analyze_job(
        sample_job_description,
        role_title="Data Analyst",
    )

    comparison = compare_candidate_to_job(
        candidate,
        job,
        job_description=sample_job_description,
    )

    print("\n========== CANDIDATE SCORING ==========")
    print("Factor scores:", comparison["factor_scores"])
    print("Factor weights:", comparison["factor_weights"])
    print("Experience breakdown:", comparison["experience_breakdown"])
    print("Overall score:", comparison["overall_score"])
    print("Candidate band:", comparison["candidate_band"])
    print("Provisional:", comparison["score_is_provisional"])
    print("Unavailable factors:", comparison["unavailable_factors"])
    print("Warnings:", comparison["warnings"])
