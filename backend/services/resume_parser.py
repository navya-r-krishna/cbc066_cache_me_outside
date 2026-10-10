
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


SECTION_ALIASES = {
    "summary": [
        "summary", "professional summary", "profile",
        "career objective", "objective", "about me",
    ],
    "skills": [
        "skills", "technical skills", "core skills",
        "key skills", "technologies", "technical expertise",
    ],
    "experience": [
        "experience", "work experience", "professional experience",
        "employment history", "work history",
    ],
    "internships": [
        "internship", "internships", "internship experience",
    ],
    "projects": [
        "projects", "academic projects",
        "personal projects", "technical projects",
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

DATE_PATTERN = re.compile(
    rf"\b(?:{MONTHS})\.?\s+\d{{4}}"
    r"|\b\d{1,2}/\d{4}\b"
    r"|\b\d{4}\b",
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

URL_PATTERN = re.compile(
    r"\b(?:https?://|www\.)\S+",
    re.IGNORECASE,
)

LINKEDIN_PATTERN = re.compile(
    r"\blinked\s*in\b\s*[:\-]?\s*\S*",
    re.IGNORECASE,
)

ADDRESS_PATTERN = re.compile(
    r"(?im)^\s*(?:address|residential address|location)"
    r"\s*[:\-]\s*.+$"
)


def normalize_text(text: str) -> str:
    """Normalize whitespace while preserving line breaks."""

    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = [
        re.sub(r"[ \t]+", " ", line).strip()
        for line in text.split("\n")
    ]

    normalized = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", normalized).strip()


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Extract selectable text from a PDF."""

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"Resume PDF not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("The uploaded file must be a PDF.")

    text_parts = []

    with fitz.open(path) as document:
        if document.is_encrypted:
            raise ValueError("The PDF is password-protected.")

        for page in document:
            page_text = page.get_text("text")

            if page_text.strip():
                text_parts.append(page_text)

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

    text_parts = []

    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        if document.is_encrypted:
            raise ValueError("The PDF is password-protected.")

        for page in document:
            page_text = page.get_text("text")

            if page_text.strip():
                text_parts.append(page_text)

    text = normalize_text("\n".join(text_parts))

    if not text:
        raise ValueError(
            "No selectable text was found. OCR may be required."
        )

    return text


def redact_pii(text: str) -> str:
    """Redact common direct identifiers before analysis."""

    text = EMAIL_PATTERN.sub("[EMAIL REDACTED]", text)
    text = URL_PATTERN.sub("[URL REDACTED]", text)
    text = LINKEDIN_PATTERN.sub("[LINKEDIN REDACTED]", text)
    text = PHONE_PATTERN.sub("[PHONE REDACTED]", text)
    text = ADDRESS_PATTERN.sub("[ADDRESS REDACTED]", text)

    return text


def identify_sections(text: str) -> dict[str, str]:
    """Split resume text using recognized section headings."""

    aliases = {
        alias.lower(): section
        for section, headings in SECTION_ALIASES.items()
        for alias in headings
    }

    sections: dict[str, list[str]] = {"general": []}
    current_section = "general"

    for line in text.splitlines():
        cleaned = line.strip().strip(":").strip()
        heading = cleaned.lower()

        if heading in aliases:
            current_section = aliases[heading]
            sections.setdefault(current_section, [])
        else:
            sections[current_section].append(line)

    return {
        section: "\n".join(lines).strip()
        for section, lines in sections.items()
        if "\n".join(lines).strip()
    }


def extract_dates(text: str) -> list[str]:
    """Extract date-like expressions."""

    return list(
        dict.fromkeys(
            match.group(0)
            for match in DATE_PATTERN.finditer(text)
        )
    )


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

    month_year = re.fullmatch(r"([a-z]+)\s+(\d{4})", value)

    if month_year:
        month_name, year_text = month_year.groups()
        month = month_names.get(month_name)

        if month:
            return int(year_text), month

    numeric_month_year = re.fullmatch(r"(\d{1,2})/(\d{4})", value)

    if numeric_month_year:
        month, year = map(int, numeric_month_year.groups())

        if 1 <= month <= 12:
            return year, month

    if re.fullmatch(r"\d{4}", value):
        return int(value), 1

    return None


def extract_date_ranges(text: str) -> list[dict[str, Any]]:
    """Extract likely date ranges from a work-history entry."""

    date_expression = (
        rf"(?:{MONTHS})\.?\s+\d{{4}}"
        r"|\d{1,2}/\d{4}"
        r"|\d{4}"
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
            1 <= start_month <= 12
            and 1 <= end_month <= 12
        ):
            continue

        start_index = start_year * 12 + start_month - 1
        end_index = end_year * 12 + end_month

        if end_index <= start_index:
            continue

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


def extract_experience_entries(
    sections: dict[str, str],
) -> list[dict[str, Any]]:
    """Extract work and internship entries separately."""

    entries = []

    for section_name in ("experience", "internships"):
        section_text = sections.get(section_name, "")

        if not section_text:
            continue

        blocks = re.split(r"\n\s*\n", section_text)

        for block in blocks:
            block = block.strip()

            if not block:
                continue

            entries.append({
                "type": (
                    "internship"
                    if section_name == "internships"
                    else "work"
                ),
                "text": block,
                "date_ranges": extract_date_ranges(block),
                "dates": extract_dates(block),
            })

    return entries


def extract_education_entries(
    sections: dict[str, str],
) -> list[str]:
    """Extract lines from the education section."""

    return [
        line.strip(" •-\t")
        for line in sections.get("education", "").splitlines()
        if line.strip(" •-\t")
    ]


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
        entry["type"] == "internship" for entry in entries
    ):
        return "internship_or_fresher"

    return "fresher_or_experience_not_detected"


def extract_resume_skills(
    text: str,
) -> list[dict[str, Any]]:
    """
    Find canonical skills using the existing skill matcher.

    Results contain canonical names, competencies, evidence, and positions.
    """

    matches = match_skills(text)
    grouped = {}

    for match in matches:
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
    education_entries = extract_education_entries(sections)

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

    # Match skills in the full redacted resume text.
    detected_skills = extract_resume_skills(analysis_text)

    return {
        "text": analysis_text,
        "sections": sections,
        "dates": extract_dates(analysis_text),
        "skills": detected_skills,
        "skill_count": len(detected_skills),
        "experience_entries": experience_entries,
        "professional_experience_months_estimated": professional_months,
        "professional_experience_years_estimated": round(
            professional_months / 12, 2
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

    raw_text = extract_text_from_pdf(pdf_path)

    return parse_resume_text(
        raw_text,
        redact_personal_info=redact_personal_info,
    )


def parse_resume_pdf_bytes(
    pdf_bytes: bytes,
    redact_personal_info: bool = True,
) -> dict[str, Any]:
    """Parse PDF bytes in memory without saving the uploaded file."""

    raw_text = extract_text_from_pdf_bytes(pdf_bytes)

    return parse_resume_text(
        raw_text,
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

    WORK EXPERIENCE
    Junior Analyst
    Example Organisation
    Mar 2025 - Present

    EDUCATION
    Bachelor of Computer Applications
    2023 - 2026

    CONTACT
    Email: candidate@example.com
    Phone: +91 98765 43210
    """

    parsed = parse_resume_text(sample_resume)
    print(json.dumps(parsed, indent=2))
