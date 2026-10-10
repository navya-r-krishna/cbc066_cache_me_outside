
from typing import Any
import re

try:
    from .resume_parser import parse_resume_text, parse_resume_pdf
except ImportError:
    from resume_parser import parse_resume_text, parse_resume_pdf


# --------------------------------------------------
# SCORING CONFIGURATION
# --------------------------------------------------

FACTOR_WEIGHTS = {
    "skills": 0.40,
    "experience": 0.30,
    "role_relevance": 0.20,
    "academics": 0.10,
}

INTERNSHIP_CREDIT = 0.50


# --------------------------------------------------
# BUILD CANDIDATE PROFILE
# --------------------------------------------------

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

    skill_names = list(dict.fromkeys(
        skill["name"]
        for skill in skills
        if skill.get("name")
    ))

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
        "project_entries": parsed.get("project_entries", []),
        "resume_summary": "\n".join(summary_parts),
        "candidate_type": parsed.get(
            "candidate_type",
            "fresher_or_experience_not_detected",
        ),
        "pii_redacted": parsed.get("pii_redacted", False),
        "warnings": parsed.get("warnings", []),
    }


# --------------------------------------------------
# EXPERIENCE REQUIREMENT EXTRACTION
# --------------------------------------------------

def extract_requested_years(
    job_description: str | None,
) -> float | None:
    """
    Extract an explicitly stated experience requirement.

    Returns:
        Positive number: minimum required years.
        0.0: freshers are explicitly welcome or no experience is required.
        None: requirement is missing or ambiguous.
    """

    if not job_description:
        return None

    text = re.sub(r"\s+", " ", job_description.casefold())

    zero_experience_patterns = [
        r"\bno\s+(?:prior\s+|previous\s+)?experience\s+"
        r"(?:is\s+)?(?:required|needed|necessary)\b",
        r"\b(?:freshers|fresh graduates|recent graduates)\s+"
        r"(?:are\s+)?welcome\b",
        r"\bentry[\s-]?level\b",
        r"\b(?:0|zero)\s+(?:years?|yrs?)\s+"
        r"(?:of\s+)?experience\b",
    ]

    for pattern in zero_experience_patterns:
        if re.search(pattern, text):
            return 0.0

    positive_patterns = [
        r"\b(?:at least|minimum of|min\.?)\s+"
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s+"
        r"(?:of\s+)?experience\b",

        r"\b(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s+"
        r"(?:of\s+)?experience\s+(?:is\s+)?"
        r"(?:required|minimum)\b",

        r"\bexperience\s+(?:of\s+)?"
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\b",

        r"\b(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)\s+"
        r"(?:of\s+)?experience\b",
    ]

    for pattern in positive_patterns:
        match = re.search(pattern, text)

        if match:
            years = float(match.group(1))

            if years > 0:
                return years

    return None


# --------------------------------------------------
# TEXT NORMALIZATION
# --------------------------------------------------

def normalize_role_terms(text: str) -> set[str]:
    """Extract meaningful words for role-relevance comparison."""

    ignored = {
        "and", "the", "for", "with", "from", "that", "this",
        "have", "has", "had", "our", "your", "senior", "junior",
        "associate", "intern", "lead", "principal", "expert",
        "years", "year", "experience", "work", "working",
        "developer", "development", "engineer", "engineering",
        "role", "position", "candidate",
    }

    return {
        word
        for word in re.findall(r"[a-z0-9+#.]+", text.casefold())
        if len(word) > 1 and word not in ignored
    }


# --------------------------------------------------
# ROLE RELEVANCE
# --------------------------------------------------

def calculate_role_relevance(
    candidate_profile: dict[str, Any],
    role_title: str,
) -> float | None:
    """
    Estimate role relevance using the resume summary, work experience,
    projects, and technical skills.

    Projects provide technical evidence but are not treated as employment.
    This is a heuristic, not semantic matching.
    """

    if not role_title or not role_title.strip():
        return None

    role = role_title.casefold()
    role_terms = normalize_role_terms(role_title)

    if not role_terms:
        return None

    summary = candidate_profile.get("resume_summary", "")
    if not isinstance(summary, str):
        summary = ""

    experience_entries = candidate_profile.get(
        "experience_entries", []
    )
    project_entries = candidate_profile.get(
        "project_entries", []
    )
    skills = candidate_profile.get("skills", [])

    def collect_entry_text(entries: list) -> str:
        parts = []

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            text = entry.get("text", "")

            if isinstance(text, str):
                parts.append(text)

        return " ".join(parts)

    experience_text = collect_entry_text(experience_entries)
    project_text = collect_entry_text(project_entries)

    summary_terms = normalize_role_terms(summary)
    experience_terms = normalize_role_terms(experience_text)
    project_terms = normalize_role_terms(project_text)

    skill_names = {
        skill.casefold().strip()
        for skill in skills
        if isinstance(skill, str)
    }

    # Measure exact role-term overlap across different evidence sources.
    evidence = []

    if summary_terms:
        evidence.append((
            len(role_terms & summary_terms) / len(role_terms),
            0.15,
        ))

    if experience_terms:
        evidence.append((
            len(role_terms & experience_terms) / len(role_terms),
            0.25,
        ))

    if project_terms:
        evidence.append((
            len(role_terms & project_terms) / len(role_terms),
            0.30,
        ))

    if skill_names:
        evidence.append((
            len(role_terms & skill_names) / len(role_terms),
            0.30,
        ))

    if not evidence:
        return None

    total_weight = sum(weight for _, weight in evidence)

    score = sum(
        value * weight
        for value, weight in evidence
    ) / total_weight

    # Role-specific technical evidence.
    # This supplements title overlap; it does not replace skill coverage.
    role_skill_groups = {
        "data": {
            "python",
            "sql",
            "pandas",
            "numpy",
            "excel",
            "google sheets",
            "data visualization",
            "machine learning",
            "scikit-learn",
            "xgboost",
            "plotly",
            "streamlit",
        },
        "backend": {
            "java",
            "spring boot",
            "node.js",
            "express.js",
            "rest apis",
            "mongodb",
            "postgresql",
            "authentication",
            "jwt",
            "api development",
            "microservices",
        },
    }

    relevant_group = None

    if any(term in role for term in (
        "data analyst",
        "data analytics",
        "data scientist",
        "data science",
        "business analyst",
    )):
        relevant_group = role_skill_groups["data"]

    elif any(term in role for term in (
        "backend",
        "back-end",
        "back end",
        "java developer",
    )):
        relevant_group = role_skill_groups["backend"]

    if relevant_group:
        project_text_lower = project_text.casefold()

        matched_role_skills = {
            skill
            for skill in relevant_group
            if skill in skill_names
            or skill in project_text_lower
        }

        if matched_role_skills:
            coverage = min(
                len(matched_role_skills) / 5,
                1.0,
            )

            score = 0.70 * score + 0.30 * coverage

    return round(
        min(max(score, 0.0), 1.0) * 100,
        2,
    )


# --------------------------------------------------
# RELEVANT INTERNSHIP DURATION
# --------------------------------------------------

def calculate_relevant_internship_months(
    candidate_profile: dict[str, Any],
    role_title: str,
) -> int:
    """Estimate the duration of internships relevant to the target role."""

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

        if not isinstance(entry_text, str):
            continue

        if not role_terms.intersection(
            normalize_role_terms(entry_text)
        ):
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
                    relevant_ranges.append(
                        (start_index, end_index)
                    )

            except (KeyError, TypeError, ValueError):
                continue

    if not relevant_ranges:
        return 0

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


# --------------------------------------------------
# ACADEMIC SCORING
# --------------------------------------------------

def calculate_academic_score(
    candidate_profile: dict[str, Any],
) -> float | None:
    """
    Academic scoring is unavailable until grades and job-specific
    qualification requirements can be compared reliably.
    """

    return None


# --------------------------------------------------
# CANDIDATE-TO-JOB COMPARISON
# --------------------------------------------------

def compare_candidate_to_job(
    candidate_profile: dict[str, Any],
    job_analysis: dict[str, Any],
    job_description: str | None = None,
) -> dict[str, Any]:
    """Compare candidate skills and calculate a provisional score."""

    candidate_skills = {
        name.casefold()
        for name in candidate_profile.get("skills", [])
        if isinstance(name, str)
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
        item["weight"]
        for item in matched_skills
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
        int(
            candidate_profile.get(
                "professional_experience_months", 0
            ) or 0
        ),
    )

    relevant_internship_months = calculate_relevant_internship_months(
        candidate_profile,
        role_title,
    )

    equivalent_experience_months = (
        professional_months
        + relevant_internship_months * INTERNSHIP_CREDIT
    )

    # Do not automatically award full experience marks to freshers.
    experience_score = None

    if requested_years is not None and requested_years > 0:
        required_months = requested_years * 12

        experience_score = round(
            min(
                equivalent_experience_months / required_months,
                1.0,
            ) * 100,
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

    # Preserve fixed weights instead of inflating missing factors.
    overall_score = None

    if available_factors:
        overall_score = round(
            sum(
                score * FACTOR_WEIGHTS[name]
                for name, score in available_factors.items()
            ),
            2,
        )

    unavailable_factors = [
        name
        for name, score in factor_scores.items()
        if score is None
    ]

    if overall_score is None:
        candidate_band = "insufficient_data"
    elif unavailable_factors:
        candidate_band = "provisional_match"
    elif overall_score >= 75:
        candidate_band = "strong_match"
    elif overall_score >= 50:
        candidate_band = "moderate_match"
    else:
        candidate_band = "developing_match"

    warnings = [
        "Detected skills do not prove proficiency.",
        "The overall score is a heuristic, not a validated hiring prediction.",
        "Unavailable factors are not rescaled; the overall score may be lower when evidence is missing.",
        "Relevant internship months receive 50% credit relative to professional experience for the experience score.",
    ]

    if requested_years == 0:
        warnings.append(
            "No prior experience is required or freshers are welcome; "
            "experience was excluded from scoring."
        )
    elif requested_years is None:
        warnings.append(
            "Experience score is unavailable because an explicit "
            "experience requirement was not extracted."
        )

    if role_score is None:
        warnings.append(
            "Role relevance could not be estimated from available "
            "summary, experience, project, or skill evidence."
        )

    if academic_score is None:
        warnings.append(
            "Academic score is unavailable because grades and "
            "job-specific qualification requirements are not assessed."
        )

    if unavailable_factors:
        warnings.append(
            "Unavailable scoring factors: "
            + ", ".join(unavailable_factors)
            + ". The overall score and candidate band are provisional."
        )

    return {
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


# --------------------------------------------------
# LOCAL TEST
# --------------------------------------------------

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

    PROJECTS

    Cricket Analytics Dashboard
    Python, Pandas, SQL
    """

    sample_job_description = """
    Data Analyst
    Required skills include Python, SQL, Pandas, and Excel.
    Machine Learning and Data Visualization are preferred.
    The candidate must have at least 2 years of experience.
    Strong communication skills are required.
    """

    candidate = build_candidate_profile(
        resume_text=sample_resume
    )

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
