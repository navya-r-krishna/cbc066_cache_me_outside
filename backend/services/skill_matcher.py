
import json
import re
from pathlib import Path
from typing import Any


DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "skills.json"
)

AMBIGUOUS_ALIASES = {
    "C", "R", "Go", "BI", "RL", "CV", "OS", "TS",
    "JS", "DL", "ML", "QA", "DSA", "NLP", "EDA",
    "K8s", "MUI", "PWA", "OIDC", "SCSS", "MSSQL",
    "MDM", "IAM", "DBMS", "ADF",
}


def load_skills() -> list[dict[str, Any]]:
    """Load and validate skills from skills.json."""

    with DATA_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    skills = data.get("skills", [])

    if not isinstance(skills, list):
        raise ValueError(
            "skills.json must contain a list under 'skills'."
        )

    seen_names = set()

    for skill in skills:
        required = ("name", "synonyms", "competency")

        if not isinstance(skill, dict) or not all(
            key in skill for key in required
        ):
            raise ValueError(f"Invalid skill entry: {skill}")

        if not isinstance(skill["name"], str) or not skill["name"].strip():
            raise ValueError(f"Invalid skill name: {skill}")

        if not isinstance(skill["synonyms"], list):
            raise ValueError(f"Synonyms must be a list: {skill}")

        if not isinstance(skill["competency"], str):
            raise ValueError(f"Invalid competency: {skill}")

        canonical = skill["name"].strip().casefold()

        if canonical in seen_names:
            raise ValueError(
                f"Duplicate canonical skill name: {skill['name']}"
            )

        seen_names.add(canonical)

    return skills


def build_pattern(term: str) -> re.Pattern:
    """Create a case-insensitive pattern with safe word boundaries."""

    escaped = re.escape(term.strip())
    escaped = escaped.replace(r"\ ", r"\s+")

    return re.compile(
        r"(?<!\w)" + escaped + r"(?!\w)",
        flags=re.IGNORECASE,
    )


def split_sentences(
    text: str,
) -> list[tuple[int, int, str]]:
    """Split sentences without breaking technical names at their dots."""

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
            sentences.append((start, end, sentence))

    return sentences


def find_sentence(
    position: int,
    sentences: list[tuple[int, int, str]],
) -> str:
    """Return the sentence containing a match."""

    for start, end, sentence in sentences:
        if start <= position < end:
            return sentence

    return ""


def has_technical_context(sentence: str) -> bool:
    """Check for technical clues in the same sentence."""

    sentence = sentence.casefold()

    cues = [
        "programming",
        "programming language",
        "developer",
        "development",
        "software",
        "coding",
        "technical skills",
        "technical stack",
        "proficiency",
        "experience with",
        "knowledge of",
        "familiar with",
        "written in",
        "built with",
        "languages:",
        "programming languages",
        "tech stack",
        "technologies",
        "frameworks",
        "libraries",
    ]

    return any(cue in sentence for cue in cues)


def has_alias_context(
    text: str,
    start: int,
    end: int,
    alias: str,
    sentences: list[tuple[int, int, str]],
) -> bool:
    """Filter ambiguous aliases using local sentence context."""

    if alias.casefold() not in {
        item.casefold() for item in AMBIGUOUS_ALIASES
    }:
        return True

    sentence = find_sentence(start, sentences)
    sentence_lower = sentence.casefold()
    alias_lower = alias.casefold()

    if alias_lower == "bi":
        # Do not treat the BI in Power BI as a separate skill.
        prefix = text[max(0, start - 12):start].casefold()

        if re.search(r"\bpower\s+$", prefix):
            return False

        # Accept the full phrase Business Intelligence.
        if "business intelligence" in sentence_lower:
            return True

        # A standalone BI abbreviation needs technical context.
        return has_technical_context(sentence)

    if alias_lower == "go":
        # Reject lowercase ordinary-language "go".
        if text[start:end] != "Go":
            return False

        after = text[end:end + 40].casefold()

        if re.match(
            r"\s+(programming|developer|development|language)\b",
            after,
        ):
            return True

        return has_technical_context(sentence)

    if alias_lower == "c":
        # C must not match inside C++ or C#.
        if end < len(text) and text[end] in "+#":
            return False

        return has_technical_context(sentence)

    if alias_lower == "r":
        return has_technical_context(sentence)

    return has_technical_context(sentence)


def match_skills(text: str) -> list[dict[str, Any]]:
    """Find skill occurrences and retain the best alias per character span."""

    if not isinstance(text, str) or not text.strip():
        return []

    skills = load_skills()
    sentences = split_sentences(text)
    results = []

    for skill in skills:
        canonical = skill["name"]
        aliases = [canonical] + skill.get("synonyms", [])

        aliases = sorted(
            {
                alias.strip()
                for alias in aliases
                if isinstance(alias, str) and alias.strip()
            },
            key=len,
            reverse=True,
        )

        matches_by_span = {}

        for alias in aliases:
            pattern = build_pattern(alias)

            for match in pattern.finditer(text):
                start, end = match.span()

                if not has_alias_context(
                    text,
                    start,
                    end,
                    alias,
                    sentences,
                ):
                    continue

                candidate = {
                    "name": canonical,
                    "competency": skill["competency"],
                    "matched_text": match.group(),
                    "alias": alias,
                    "start": start,
                    "end": end,
                    "sentence": find_sentence(start, sentences),
                }

                span = (start, end)
                existing = matches_by_span.get(span)

                if existing is None:
                    matches_by_span[span] = candidate
                else:
                    candidate_rank = (
                        alias.casefold() != canonical.casefold(),
                        -len(alias),
                    )
                    existing_rank = (
                        existing["alias"].casefold()
                        != canonical.casefold(),
                        -len(existing["alias"]),
                    )

                    if candidate_rank < existing_rank:
                        matches_by_span[span] = candidate

        results.extend(matches_by_span.values())

    results.sort(
        key=lambda item: (
            item["start"],
            item["end"],
            item["name"],
        )
    )

    return results


if __name__ == "__main__":
    examples = [
        "Python is required. Python is used for automation.",
        "I use C++ and C# professionally.",
        "I like to go running in the morning.",
        "We need Go programming for backend development.",
        "Experience with Node.js and .NET is preferred.",
        "Power BI reporting and Business Intelligence analysis.",
        "The candidate has C programming and R programming experience.",
    ]

    for example in examples:
        print(f"\nText: {example}")

        matches = match_skills(example)

        if not matches:
            print("  No skills found.")
            continue

        for item in matches:
            print(
                f"  {item['name']} "
                f"(matched: {item['matched_text']!r}, "
                f"position: {item['start']}-{item['end']})"
            )
            print(f"    Evidence: {item['sentence']}")
