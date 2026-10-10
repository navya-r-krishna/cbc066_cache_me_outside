
try:
    from Backend.services.candidate_profile import (
        calculate_role_relevance,
        extract_requested_years,
        calculate_relevant_internship_months,
    )
    from Backend.services.resume_parser import (
        extract_dates,
        extract_date_ranges,
        parse_resume_text,
    )
except ImportError:
    try:
        from backend.services.candidate_profile import (
            calculate_role_relevance,
            extract_requested_years,
            calculate_relevant_internship_months,
        )
        from backend.services.resume_parser import (
            extract_dates,
            extract_date_ranges,
            parse_resume_text,
        )
    except ImportError:
        from services.candidate_profile import (
            calculate_role_relevance,
            extract_requested_years,
            calculate_relevant_internship_months,
        )
        from services.resume_parser import (
            extract_dates,
            extract_date_ranges,
            parse_resume_text,
        )




# --------------------------------------------------
# EXISTING CANDIDATE PROFILE TESTS
# --------------------------------------------------

def test_extract_requested_years():
    assert extract_requested_years(
        "At least 2 years of experience required"
    ) == 2.0


def test_extract_requested_years_missing():
    assert extract_requested_years(
        "Experience with Python preferred"
    ) is None


def test_role_relevance_uses_experience_title():
    profile = {
        "resume_summary": "Interested in data and technology",
        "experience_entries": [
            {
                "type": "internship",
                "text": "Data Analyst Intern\nExample Company",
                "date_ranges": [],
            }
        ],
    }

    score = calculate_role_relevance(profile, "Data Analyst")

    assert score is not None
    assert score > 0


def test_role_relevance_without_evidence():
    profile = {
        "resume_summary": "",
        "experience_entries": [],
    }

    assert calculate_role_relevance(profile, "Data Analyst") is None


def test_relevant_internship_months():
    profile = {
        "experience_entries": [
            {
                "type": "internship",
                "text": "Data Analyst Intern",
                "date_ranges": [
                    {
                        "start": {"year": 2025, "month": 1},
                        "end": {"year": 2025, "month": 6},
                    }
                ],
            }
        ],
    }

    assert calculate_relevant_internship_months(
        profile, "Data Analyst"
    ) == 6


def test_unrelated_role_has_low_relevance():
    profile = {
        "resume_summary": "Experienced data analyst using Python and SQL.",
        "experience_entries": [
            {
                "type": "internship",
                "text": "Data Analyst Intern Python SQL",
                "date_ranges": [],
            }
        ],
    }

    score = calculate_role_relevance(
        profile, "Cybersecurity Engineer"
    )

    assert score is not None
    assert score < 50


def test_overlapping_internships_are_not_double_counted():
    profile = {
        "experience_entries": [
            {
                "type": "internship",
                "text": "Data Analyst Intern",
                "date_ranges": [
                    {
                        "start": {"year": 2025, "month": 1},
                        "end": {"year": 2025, "month": 6},
                    }
                ],
            },
            {
                "type": "internship",
                "text": "Junior Data Analyst",
                "date_ranges": [
                    {
                        "start": {"year": 2025, "month": 3},
                        "end": {"year": 2025, "month": 8},
                    }
                ],
            },
        ],
    }

    assert calculate_relevant_internship_months(
        profile, "Data Analyst"
    ) == 8


def test_missing_internship_dates_return_zero():
    profile = {
        "experience_entries": [
            {
                "type": "internship",
                "text": "Data Analyst Intern",
                "date_ranges": [],
            }
        ],
    }

    assert calculate_relevant_internship_months(
        profile, "Data Analyst"
    ) == 0


# --------------------------------------------------
# NEW RESUME PARSER REGRESSION TESTS
# --------------------------------------------------

def test_projects_with_technology_headings_are_split():
    resume = """
    PROJECTS
    Cricket Analytics Platform | Python, Pandas, SQL | GitHub
    Built cricket analytics dashboards.
    WPL Win Probability Model | Python, Scikit-learn | GitHub
    Achieved 90.98% accuracy.
    Intelligent Document Query Assistant | Python, LangChain | GitHub
    Built a PDF question-answering assistant.
    """

    parsed = parse_resume_text(resume, redact_personal_info=False)
    projects = parsed["project_entries"]

    assert len(projects) == 3
    assert "Cricket Analytics Platform" in projects[0]["text"]
    assert "WPL Win Probability Model" in projects[1]["text"]
    assert "Intelligent Document Query Assistant" in projects[2]["text"]


def test_activities_are_separate_from_projects_and_experience():
    resume = """
    PROJECTS
    Cricket Analytics Platform | Python, Pandas | GitHub
    Built a cricket analytics dashboard.

    ACTIVITIES
    CIE IGNITE 2026 Hackathon - Top 21 Finalist
    MYSTARA 24 Hour Hackathon - Volunteering
    Participated in the KSCA Open Age T20 League (2026)
    """

    parsed = parse_resume_text(resume, redact_personal_info=False)

    assert len(parsed["project_entries"]) == 1
    assert len(parsed["activities"]) == 3
    assert parsed["experience_entries"] == []

    activity_text = " ".join(
        entry["text"] for entry in parsed["activities"]
    )
    assert "CIE IGNITE" in activity_text
    assert "MYSTARA" in activity_text
    assert "KSCA" in activity_text

    project_text = " ".join(
        entry["text"] for entry in parsed["project_entries"]
    )
    assert "CIE IGNITE" not in project_text


def test_decimal_metrics_are_not_extracted_as_dates():
    text = """
    Model accuracy: 90.98%
    ROC-AUC: 0.9666
    Education: 2024 - 2027
    """

    dates = extract_dates(text)

    assert "9666" not in dates
    assert "2024" in dates
    assert "2027" in dates


def test_date_ranges_ignore_decimal_metrics():
    text = """
    Model evaluation achieved 0.9666 ROC-AUC.
    Education: 2024 - 2027.
    Internship: Jan 2025 - Jun 2025.
    """

    ranges = extract_date_ranges(text)

    assert len(ranges) == 2
    assert all(
        item["start"]["year"] != 9666
        and item["end"]["year"] != 9666
        for item in ranges
    )


def test_projects_do_not_count_as_professional_experience():
    resume = """
    PROJECTS
    Cricket Analytics Platform | Python, Pandas | GitHub
    Built an analytics platform.
    WPL Win Probability Model | Python, Scikit-learn | GitHub
    Achieved 90.98% accuracy.

    ACTIVITIES
    CIE IGNITE 2026 Hackathon - Top 21 Finalist
    """

    parsed = parse_resume_text(resume, redact_personal_info=False)

    assert len(parsed["project_entries"]) == 2
    assert parsed["experience_entries"] == []
    assert parsed["professional_experience_months_estimated"] == 0
