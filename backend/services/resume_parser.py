
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import fitz

try:
    from .skill_matcher import match_skills
except ImportError:
    from skill_matcher import match_skills


# --------------------------------------------------
# SECTION HEADINGS
# --------------------------------------------------

SECTION_ALIASES = {
    "summary": [
        "summary", "professional summary", "profile",
        "career objective", "objective", "about me",
    ],
    "skills": [
        "skills", "technical skills", "core skills",
        "key skills", "technologies", "technical expertise",
        "technical competencies",
    ],
    "experience": [
        "experience", "work experience", "professional experience",
        "employment history", "work history", "professional background",
    ],
    "internships": [
        "internship", "internships", "internship experience",
        "internship experiences",
    ],
    "projects": [
        "projects", "academic projects", "personal projects",
        "technical projects", "project experience", "key projects",
        "selected projects",
    ],
    "activities": [
        "activities", "extracurricular activities",
        "extra curricular activities", "leadership and activities",
        "achievements and activities", "positions of responsibility",
        "volunteering", "volunteer experience",
    ],
    "education": [
        "education", "academic background",
        "educational qualifications", "qualifications",
    ],
    "certifications": [
        "certifications", "certificates",
        "licenses and certifications",
    ],
    "contact": [
        "contact", "contact information",
        "personal details", "personal information",
    ],
}

MONTHS = (
    "jan|january|feb|february|mar|march|apr|april|may|"
    "jun|june|jul|july|aug|august|sep|sept|september|"
    "oct|october|nov|november|dec|december"
)

# Restrict standalone years to a realistic range.
# This prevents the "9666" part of 0.9666 from becoming a year.
YEAR_PATTERN = r"(?:19\d{2}|20\d{2})"

DATE_PATTERN = re.compile(
    rf"\b(?:{MONTHS})\.?\s+{YEAR_PATTERN}\b"
    rf"|\b(?:0?[1-9]|1[0-2])/{YEAR_PATTERN}\b"
    rf"|(?<![\d.]){YEAR_PATTERN}(?![\d.]|\d)",
    re.IGNORECASE,
)

EMAIL_PATTERN = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)
PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:\+?\d{1,3}[-.\s]?)?"
    r"(?:\(?\d{2,5}\)?[-.\s]?)"
    r"\d{3,5}[-.\s]?\d{3,5}(?!\w)"
)
URL_PATTERN = re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE)
LINKEDIN_PATTERN = re.compile(
    r"\blinked\s*in\b\s*[:\-]?\s*\S+",
    re.IGNORECASE,
)
ADDRESS_PATTERN = re.compile(
    r"(?im)^\s*(?:address|residential address|location)"
    r"\s*[:\-]\s*.+$"
)


# --------------------------------------------------
# TEXT NORMALIZATION AND PDF EXTRACTION
# --------------------------------------------------

def normalize_text(text: str) -> str:
    """Normalize whitespace while preserving line breaks."""
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [
        re.sub(r"[ \t]+", " ", line).strip()
        for line in text.split("\n")
    ]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Extract selectable text from a PDF file."""
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"Resume PDF not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError("The uploaded file must be a PDF.")

    with fitz.open(path) as document:
        if document.is_encrypted:
            raise ValueError("The PDF is password-protected.")
        text_parts = [
            page.get_text("text")
            for page in document
            if page.get_text("text").strip()
        ]

    text = normalize_text("\n".join(text_parts))
    if not text:
        raise ValueError(
            "No selectable text was found. The PDF may require OCR."
        )
    return text


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract PDF text from memory without saving the upload."""
    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")

    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        if document.is_encrypted:
            raise ValueError("The PDF is password-protected.")
        text_parts = [
            page.get_text("text")
            for page in document
            if page.get_text("text").strip()
        ]

    text = normalize_text("\n".join(text_parts))
    if not text:
        raise ValueError(
            "No selectable text was found. OCR may be required."
        )
    return text


# --------------------------------------------------
# PERSONAL INFORMATION REDACTION
# --------------------------------------------------

def redact_pii(text: str) -> str:
    """Redact common direct identifiers before analysis."""
    text = EMAIL_PATTERN.sub("[EMAIL REDACTED]", text)
    text = URL_PATTERN.sub("[URL REDACTED]", text)
    text = LINKEDIN_PATTERN.sub("[LINKEDIN REDACTED]", text)
    text = PHONE_PATTERN.sub("[PHONE REDACTED]", text)
    text = ADDRESS_PATTERN.sub("[ADDRESS REDACTED]", text)
    return text


# --------------------------------------------------
# SECTION IDENTIFICATION
# --------------------------------------------------

def identify_sections(text: str) -> dict[str, str]:
    """Identify resume sections, including spaced-out headings."""
    aliases = {
        alias.casefold().strip(): section
        for section, headings in SECTION_ALIASES.items()
        for alias in headings
    }
    compact_aliases = {
        re.sub(r"\s+", "", alias): section
        for alias, section in aliases.items()
    }

    sections: dict[str, list[str]] = {"general": []}
    current_section = "general"

    for line in text.splitlines():
        cleaned = line.strip().strip(":").strip()
        heading = cleaned.casefold()
        compact_heading = re.sub(r"\s+", "", heading)

        if heading in aliases:
            current_section = aliases[heading]
            sections.setdefault(current_section, [])
        elif compact_heading in compact_aliases:
            current_section = compact_aliases[compact_heading]
            sections.setdefault(current_section, [])
        else:
            sections[current_section].append(line)

    return {
        name: content
        for name, lines in sections.items()
        if (content := "\n".join(lines).strip())
    }


# --------------------------------------------------
# DATE EXTRACTION
# --------------------------------------------------

def extract_dates(text: str) -> list[str]:
    """Extract realistic date-like expressions, excluding decimals."""
    return list(dict.fromkeys(
        match.group(0)
        for match in DATE_PATTERN.finditer(text)
    ))


def parse_date(value: str) -> tuple[int, int] | None:
    """Convert a supported date expression into (year, month)."""
    value = value.strip().lower().replace(".", "")

    if value in {"present", "current", "now"}:
        today = date.today()
        return today.year, today.month

    month_names = {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "sept": 9, "september": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12,
    }

    month_year = re.fullmatch(
        rf"([a-z]+)\s+({YEAR_PATTERN})", value
    )
    if month_year:
        month_name, year_text = month_year.groups()
        month = month_names.get(month_name)
        if month:
            return int(year_text), month

    numeric_month_year = re.fullmatch(
        rf"(\d{{1,2}})/({YEAR_PATTERN})", value
    )
    if numeric_month_year:
        month, year = map(int, numeric_month_year.groups())
        if 1 <= month <= 12:
            return year, month

    if re.fullmatch(YEAR_PATTERN, value):
        return int(value), 1

    return None


def extract_date_ranges(text: str) -> list[dict[str, Any]]:
    """Extract likely date ranges without interpreting decimals as years."""
    date_expression = (
        rf"(?:{MONTHS})\.?\s+{YEAR_PATTERN}"
        rf"|\d{{1,2}}/{YEAR_PATTERN}"
        rf"|{YEAR_PATTERN}"
    )
    pattern = re.compile(
        rf"(?P<start>{date_expression})"
        rf"\s*(?:-|–|—|\bto\b)\s*"
        rf"(?P<end>present|current|now|{date_expression})",
        re.IGNORECASE,
    )

    ranges = []
    for match in pattern.finditer(text):
        start = parse_date(match.group("start"))
        end_text = match.group("end").strip()
        end = parse_date(end_text)

        if start is None or end is None or end < start:
            continue

        ranges.append({
            "start_text": match.group("start"),
            "end_text": end_text,
            "start": {"year": start[0], "month": start[1]},
            "end": {"year": end[0], "month": end[1]},
            "is_current": end_text.lower() in {
                "present", "current", "now"
            },
        })
    return ranges


def calculate_non_overlapping_experience_months(
    date_ranges: list[dict[str, Any]],
) -> int:
    """Calculate the union of date ranges without double-counting."""
    intervals = []

    for item in date_ranges:
        try:
            start_year = int(item["start"]["year"])
            start_month = int(item["start"]["month"])
            end_year = int(item["end"]["year"])
            end_month = int(item["end"]["month"])
        except (KeyError, TypeError, ValueError):
            continue

        if not (
            1 <= start_month <= 12 and 1 <= end_month <= 12
        ):
            continue

        start_index = start_year * 12 + start_month - 1
        end_index = end_year * 12 + end_month

        if end_index > start_index:
            intervals.append((start_index, end_index))

    if not intervals:
        return 0

    intervals.sort()
    total = 0
    current_start, current_end = intervals[0]

    for start, end in intervals[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            total += current_end - current_start
            current_start, current_end = start, end

    return total + current_end - current_start


# --------------------------------------------------
# ENTRY EXTRACTION
# --------------------------------------------------

def _make_entry(text: str, entry_type: str) -> dict[str, Any]:
    return {
        "type": entry_type,
        "text": text.strip(),
        "date_ranges": extract_date_ranges(text),
        "dates": extract_dates(text),
    }


def extract_entries_from_section(
    section_text: str,
    entry_type: str,
) -> list[dict[str, Any]]:
    """Split ordinary sections on blank lines."""
    if not section_text.strip():
        return []

    blocks = re.split(r"\n\s*\n", section_text.strip())
    return [
        _make_entry(block, entry_type)
        for block in blocks
        if block.strip()
    ]


# Recognize headings formatted like:
# Project Name | Python, Pandas, SQL | GitHub
PROJECT_TITLE_PATTERN = re.compile(
    r"^\s*(?P<title>[^|\n]{4,}?)\s*\|\s*"
    r"(?P<technologies>[^|\n]{2,})"
    r"(?:\s*\|\s*.*)?$",
    re.IGNORECASE,
)

ACTIVITY_PATTERN = re.compile(
    r"\b(?:hackathon|volunteering|volunteer|finalist|"
    r"extracurricular|cricket league|participated in|"
    r"student club|event coordinator)\b",
    re.IGNORECASE,
)


def _is_project_title(line: str) -> bool:
    match = PROJECT_TITLE_PATTERN.match(line.strip())
    if not match:
        return False

    title = match.group("title").strip()
    technologies = match.group("technologies").strip()

    # Avoid interpreting ordinary prose containing a pipe as a title.
    return (
        len(title) >= 4
        and len(technologies) >= 2
        and not ACTIVITY_PATTERN.search(title)
    )



def extract_project_entries(
    sections: dict[str, str],
) -> list[dict[str, Any]]:
    """Extract projects while handling wrapped titles and activity lines."""
    text = sections.get("projects", "").strip()
    if not text:
        return []

    lines = [line.strip() for line in text.splitlines()]

    # Separate activity lines that were accidentally placed in Projects.
    project_lines = []
    extracted_activities = []

    for line in lines:
        if not line:
            project_lines.append("")
        elif ACTIVITY_PATTERN.search(line):
            extracted_activities.append(_make_entry(line, "activity"))
        else:
            project_lines.append(line)

    # A project title can wrap across two PDF lines:
    # "Cricket Analytics Platform | Python,"
    # "SQL, Pandas, Streamlit | GitHub"
    merged_lines = []
    i = 0

    while i < len(project_lines):
        line = project_lines[i]

        if (
            i + 1 < len(project_lines)
            and "|" in line
            and line.rstrip().endswith(",")
            and "|" not in project_lines[i + 1]
        ):
            line = line + " " + project_lines[i + 1]
            i += 1

        merged_lines.append(line)
        i += 1

    entries = []
    current_lines = []
    found_title = False

    def flush():
        nonlocal current_lines
        content = "\n".join(current_lines).strip()
        if content:
            entries.append(_make_entry(content, "project"))
        current_lines = []

    for line in merged_lines:
        if _is_project_title(line):
            found_title = True
            flush()
            current_lines.append(line)
        else:
            current_lines.append(line)

    flush()

    # Keep activities available to the parser's activities field.
    # This function cannot update the sections dictionary, so the
    # parser will collect these through the helper below.
    sections["_extracted_project_activities"] = "\n".join(
        entry["text"] for entry in extracted_activities
    )

    if found_title:
        return entries

    # Fall back to blank-line splitting if no title pattern was found.
    return extract_entries_from_section(
        "\n".join(project_lines), "project"
    )



def extract_experience_entries(
    sections: dict[str, str],
) -> list[dict[str, Any]]:
    """Extract work and internship entries, excluding projects/activities."""
    entries = []

    for section_name in ("experience", "internships"):
        entry_type = (
            "internship" if section_name == "internships" else "work"
        )
        entries.extend(
            extract_entries_from_section(
                sections.get(section_name, ""),
                entry_type,
            )
        )

    return entries


def extract_activity_entries(
    sections: dict[str, str],
) -> list[dict[str, Any]]:
    """Extract extracurricular activities and hackathon entries."""
    text = sections.get("activities", "").strip()
    if not text:
        return []

    # Keep each activity line distinct unless a blank-line block is
    # clearly being used as a multi-line activity description.
    lines = [line.strip(" •-\t") for line in text.splitlines()]
    lines = [line for line in lines if line]

    return [_make_entry(line, "activity") for line in lines]


def extract_education_entries(sections: dict[str, str]) -> list[str]:
    """Extract lines from the education section."""
    return [
        line.strip(" •-\t")
        for line in sections.get("education", "").splitlines()
        if line.strip(" •-\t")
    ]


# --------------------------------------------------
# CANDIDATE CLASSIFICATION
# --------------------------------------------------

def classify_candidate(
    professional_months: int,
    internship_months: int,
    entries: list[dict[str, Any]],
) -> str:
    """Estimate a broad experience category."""
    if professional_months >= 60:
        return "experienced"
    if professional_months >= 24:
        return "early_career_or_mid_level"
    if professional_months > 0:
        return "entry_level_or_early_career"
    if internship_months > 0 or any(
        entry.get("type") == "internship" for entry in entries
    ):
        return "internship_or_fresher"
    return "fresher_or_experience_not_detected"


# --------------------------------------------------
# SKILL EXTRACTION
# --------------------------------------------------

def extract_resume_skills(text: str) -> list[dict[str, Any]]:
    """Find canonical skills using the existing skill matcher."""
    grouped: dict[str, dict[str, Any]] = {}

    for match in match_skills(text):
        name = match["name"]

        if name not in grouped:
            grouped[name] = {
                "name": name,
                "competency": match["competency"],
                "mention_count": 0,
                "evidence": [],
                "positions": [],
            }

        grouped[name]["mention_count"] += 1

        if match["sentence"] not in grouped[name]["evidence"]:
            grouped[name]["evidence"].append(match["sentence"])

        grouped[name]["positions"].append({
            "start": match["start"],
            "end": match["end"],
        })

    return sorted(
        grouped.values(),
        key=lambda skill: skill["name"].lower(),
    )


# --------------------------------------------------
# MAIN RESUME PARSER
# --------------------------------------------------


def parse_resume_text(
    raw_text: str,
    redact_personal_info: bool = True,
) -> dict[str, Any]:
    """Parse pasted resume text without persisting it."""
    if not isinstance(raw_text, str):
        raise TypeError("Resume text must be a string.")

    normalized_text = normalize_text(raw_text)
    if not normalized_text:
        raise ValueError("Resume text is empty.")

    analysis_text = (
        redact_pii(normalized_text)
        if redact_personal_info
        else normalized_text
    )

    sections = identify_sections(analysis_text)

    experience_entries = extract_experience_entries(sections)

    project_entries = extract_project_entries(sections)

    activity_entries = extract_activity_entries(sections)

    # Merge activity lines that were found inside the Projects section.
    embedded_activities = sections.pop(
        "_extracted_project_activities", ""
    )

    if embedded_activities:
        activity_entries.extend(
            _make_entry(line, "activity")
            for line in embedded_activities.splitlines()
            if line.strip()
        )

    education_entries = extract_education_entries(sections)

    # Only work and internship entries contribute to experience estimates.
    professional_ranges = []
    internship_ranges = []

    for entry in experience_entries:
        if entry["type"] == "internship":
            internship_ranges.extend(entry["date_ranges"])
        else:
            professional_ranges.extend(entry["date_ranges"])

    professional_months = calculate_non_overlapping_experience_months(
        professional_ranges
    )

    internship_months = calculate_non_overlapping_experience_months(
        internship_ranges
    )

    detected_skills = extract_resume_skills(analysis_text)

    return {
        "text": analysis_text,
        "sections": sections,
        "dates": extract_dates(analysis_text),
        "skills": detected_skills,
        "skill_count": len(detected_skills),
        "experience_entries": experience_entries,
        "project_entries": project_entries,
        "activities": activity_entries,
        "professional_experience_months_estimated": professional_months,
        "professional_experience_years_estimated": round(
            professional_months / 12,
            2,
        ),
        "internship_experience_months_estimated": internship_months,
        "education": education_entries,
        "candidate_type": classify_candidate(
            professional_months,
            internship_months,
            experience_entries,
        ),
        "pii_redacted": redact_personal_info,
        "warnings": [
            "Skills are limited to those in the current skills dictionary.",
            "Experience estimates depend on recognizable work-history "
            "sections and date formats.",
            "Projects are extracted separately and are not counted as "
            "professional employment.",
            "Activities are extracted separately from projects and "
            "professional employment.",
            "Overlapping periods are counted once within each category.",
            "Scanned PDFs may require OCR.",
            "PII redaction is best-effort and does not guarantee that "
            "all personal identifiers are removed.",
        ],
    }

def parse_resume_pdf(
    pdf_path: str | Path,
    redact_personal_info: bool = True,
) -> dict[str, Any]:
    """Parse a PDF resume."""
    return parse_resume_text(
        extract_text_from_pdf(pdf_path),
        redact_personal_info=redact_personal_info,
    )


def parse_resume_pdf_bytes(
    pdf_bytes: bytes,
    redact_personal_info: bool = True,
) -> dict[str, Any]:
    """Parse PDF bytes in memory without saving the upload."""
    return parse_resume_text(
        extract_text_from_pdf_bytes(pdf_bytes),
        redact_personal_info=redact_personal_info,
    )


if __name__ == "__main__":
    sample_resume = """
    PROFESSIONAL SUMMARY
    BCA student with experience in Python and SQL.

    TECHNICAL SKILLS
    Python, SQL, Pandas, Machine Learning

    INTERNSHIPS
    Data Analyst Intern
    Example Company
    Jan 2025 - Jun 2025

    PROJECTS
    Cricket Analytics Dashboard | Python, Pandas, SQL | GitHub
    Built an analytics dashboard.
    WPL Prediction Model | Python, Scikit-learn | GitHub
    Achieved 90.98% accuracy and 0.9666 ROC-AUC.

    ACTIVITIES
    CIE IGNITE 2026 Hackathon - Top 21 Finalist
    Participated in the KSCA Open Age T20 League (2026)

    EDUCATION
    Bachelor of Computer Applications
    2023 - 2026
    """

    print(json.dumps(parse_resume_text(sample_resume), indent=2))
