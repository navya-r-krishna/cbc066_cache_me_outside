
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
    """Load and validate the skill dictionary."""

    with DATA_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    skills = data.get("skills", [])

    if not isinstance(skills, list):
        raise ValueError(
            "skills.json must contain a list under 'skills'."
        )

    seen_names = set()

    for skill in skills:
        if not isinstance(skill, dict):
            raise ValueError(f"Invalid skill entry: {skill}")

        required = ("name", "synonyms", "competency")
        if not all(key in skill for key in required):
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
    """Match complete aliases without matching inside larger words."""

    escaped = re.escape(term.strip())
    escaped = escaped.replace(r"\ ", r"\s+")

    return re.compile(
        r"(?<!\w)" + escaped + r"(?!\w)",
        flags=re.IGNORECASE,
    )


def split_sentences(text: str) -> list[tuple[int, int, str]]:
    """Split sentences while preserving offsets."""

    protected = re.sub(
        r"(?i)(?<!\w)(?:Node\.js|React\.js|Next\.js|Vue\.js|\.NET)",
        lambda match: match.group().replace(".", "\u0001"),
        text,
    )

    pattern = re.compile(r"[^.!?\n]+(?:[.!?]+|(?=\n)|$)")
    sentences = []

    for match in pattern.finditer(protected):
        start, end = match.span()
        raw_sentence = text[start:end]
        sentence = raw_sentence.strip()

        if not sentence:
            continue

        leading = len(raw_sentence) - len(raw_sentence.lstrip())
        actual_start = start + leading
        actual_end = actual_start + len(sentence)

        sentences.append((actual_start, actual_end, sentence))

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
    """Check for nearby technical clues."""

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
    """Filter ambiguous aliases using local context."""

    alias_lower = alias.casefold()
    sentence = find_sentence(start, sentences)
    sentence_lower = sentence.casefold()

    # Do not match JS inside Node.js, React.js, Next.js, etc.
    if alias_lower == "js":
        if start > 0 and text[start - 1] == ".":
            return False

    # Handle ambiguous short aliases.
    if alias_lower in {"bi", "bi reporting", "c", "r", "go", "ts", "ml", "dl"}:

        # BI / BI Reporting
        if alias_lower in {"bi", "bi reporting"}:
            prefix = text[max(0, start - 20):start].casefold()

            # Prevent "BI reporting" from matching inside
            # "Power BI reporting".
            if re.search(r"\bpower\s+$", prefix):
                return False

            # Accept the full phrase Business Intelligence.
            if "business intelligence" in sentence_lower:
                return True

            return has_technical_context(sentence)

        # Go programming language
        if alias_lower == "go":
            # Reject ordinary lowercase "go".
            if text[start:end] != "Go":
                return False

            after = text[end:end + 40].casefold()

            if re.match(
                r"\s+(programming|developer|development|language)\b",
                after,
            ):
                return True

            return has_technical_context(sentence)

        # C programming language
        if alias_lower == "c":
            # Never match C inside C++ or C#.
            if end < len(text) and text[end] in "+#":
                return False

            return has_technical_context(sentence)

        # R programming language
        if alias_lower == "r":
            return has_technical_context(sentence)

        # Other ambiguous abbreviations.
        return has_technical_context(sentence)

    return True

def match_skills(text: str) -> list[dict[str, Any]]:
    """Find skill occurrences and suppress overlapping aliases."""

    if not isinstance(text, str) or not text.strip():
        return []

    skills = load_skills()
    sentences = split_sentences(text)
    url_pattern = re.compile(r"https?://\S+", re.IGNORECASE)
    url_ranges = [m.span() for m in url_pattern.finditer(text)]

    candidates = []

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

        for alias in aliases:
            pattern = build_pattern(alias)

            for match in pattern.finditer(text):
                start, end = match.span()

                if any(
                    url_start <= start < url_end
                    for url_start, url_end in url_ranges
                ):
                    continue

                if not has_alias_context(
                    text, start, end, alias, sentences
                ):
                    continue

                candidates.append({
                    "name": canonical,
                    "competency": skill["competency"],
                    "matched_text": match.group(),
                    "alias": alias,
                    "start": start,
                    "end": end,
                    "sentence": find_sentence(start, sentences),
                })

    # Prefer the longest span at a given location. This prevents
    # "C programming" and "C" being counted twice at the same start.
    candidates.sort(
        key=lambda item: (
            item["start"],
            -(item["end"] - item["start"]),
            item["alias"].casefold() != item["name"].casefold(),
        )
    )

    results = []

    for candidate in candidates:
        start, end = candidate["start"], candidate["end"]

        # Suppress a shorter overlapping alias, such as "C" when
        # "C programming" already matched the same span.
        overlaps = any(
            candidate["name"] == existing["name"]
            and start < existing["end"]
            and end > existing["start"]
            for existing in results
        )

        if not overlaps:
            results.append(candidate)

    results.sort(key=lambda item: (item["start"], item["end"], item["name"]))
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
        "JavaScript and JS are required.",
        "My profile: https://github.com/example",
        "Version Control and Tools: Git, GitHub, VS Code, Postman",
    ]

    for example in examples:
        print(f"\nText: {example}")

        for item in match_skills(example):
            print(
                f"  {item['name']} "
                f"(matched: {item['matched_text']!r}, "
                f"position: {item['start']}-{item['end']})"
            )
            print(f"    Evidence: {item['sentence']}")
