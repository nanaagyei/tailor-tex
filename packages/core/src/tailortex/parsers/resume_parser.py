"""Deterministic resume text parser.

Extracts structured sections from raw resume text using pattern matching.
This is the rule-based fallback — no LLM required.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

from tailortex.schemas.profile import (
    Bullet,
    CanonicalProfile,
    Education,
    Experience,
    Link,
    Owner,
    Project,
    Skill,
    Source,
)


@dataclass
class ParserWarning:
    section: str
    message: str
    line: int | None = None


@dataclass
class ProfileDraft:
    profile: CanonicalProfile
    raw_text: str
    warnings: list[ParserWarning] = field(default_factory=list)
    confidence: dict[str, float] = field(default_factory=dict)


# Section heading patterns (case-insensitive)
_SECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    "contact": re.compile(
        r"^(?:contact\s*(?:info(?:rmation)?)?|personal\s*(?:info(?:rmation)?)?)$",
        re.IGNORECASE,
    ),
    "summary": re.compile(
        r"^(?:summary|profile|objective|about(?:\s*me)?|professional\s*summary)$",
        re.IGNORECASE,
    ),
    "experience": re.compile(
        r"^(?:(?:work\s*)?experience|employment(?:\s*history)?|"
        r"professional\s*experience|career\s*(?:history|experience)|"
        r"work\s*history|relevant\s*experience)$",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^(?:education|academic(?:\s*background)?|academic\s*history)$",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"^(?:(?:technical\s*)?skills|technologies|competenc(?:ies|es)|"
        r"core\s*(?:skills|competenc(?:ies|es))|technical\s*proficienc(?:y|ies))$",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"^(?:(?:selected\s*|personal\s*|side\s*|key\s*|notable\s*)?projects)$",
        re.IGNORECASE,
    ),
    "certifications": re.compile(
        r"^(?:certifications?|licenses?(?:\s*(?:and|&)\s*certifications?)?)$",
        re.IGNORECASE,
    ),
}

# Zero-width and invisible unicode characters to strip
_INVISIBLE_CHARS = re.compile(r"[\u200b\u200c\u200d\u200e\u200f\ufeff\u00ad\u2060\u2063]")

# Date patterns — match full and abbreviated month names
_MONTH_NAMES = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)

_DATE_PATTERN = re.compile(
    rf"(?:{_MONTH_NAMES}\.?\s*\d{{4}}|\d{{4}}[-/]\d{{2}}|\d{{4}})",
    re.IGNORECASE,
)

_DATE_RANGE_PATTERN = re.compile(
    rf"({_MONTH_NAMES}\.?\s*\d{{4}}|\d{{4}}[-/]\d{{2}}|\d{{4}})"
    rf"\s*[-—]+\s*"
    rf"({_MONTH_NAMES}\.?\s*\d{{4}}|\d{{4}}[-/]\d{{2}}|\d{{4}}|[Pp]resent|[Cc]urrent|[Nn]ow)",
    re.IGNORECASE,
)

# Standalone end-date at end of line (e.g., "Software QA Engineer    Present")
_TRAILING_DATE_PATTERN = re.compile(
    rf"^(.+?)\s{{2,}}({_MONTH_NAMES}\.?\s*\d{{4}}|\d{{4}}|[Pp]resent|[Cc]urrent|[Nn]ow)\s*$",
    re.IGNORECASE,
)

# Standalone present/current/now (a line that is just a date word)
_STANDALONE_PRESENT = re.compile(r"^(?:Present|Current|Now)\s*$", re.IGNORECASE)

_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_PATTERN = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
_URL_PATTERN = re.compile(
    r"https?://[^\s,;]+|(?:linkedin\.com|github\.com|[a-z]+\.[a-z]{2,})/[^\s,;]*"
)
_BULLET_PATTERN = re.compile(r"^\s*[•\-\*\u2022\u25E6\u25AA\u2023\u25CF\u25CB▪►]\s*(.+)")
# "Title | Company" or "Title  |  Company" pattern
_PIPE_TITLE_PATTERN = re.compile(r"^(.+?)\s*\|\s*(.+)$")

_MONTH_MAP = {
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
}


def _uid(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


def _clean(text: str) -> str:
    """Strip invisible unicode characters and normalize whitespace."""
    text = _INVISIBLE_CHARS.sub("", text)
    # Collapse multiple spaces into one (but preserve leading indent)
    text = re.sub(r"(?<=\S) {2,}", "  ", text)
    return text.strip()


def _normalize_date(raw: str) -> str | None:
    """Convert various date formats to YYYY-MM or YYYY."""
    raw = raw.strip()
    if raw.lower() in ("present", "current", "now"):
        return None

    if re.match(r"^\d{4}[-/]\d{2}$", raw):
        return raw.replace("/", "-")

    if re.match(r"^\d{4}$", raw):
        return raw

    m = re.match(r"([A-Za-z]+)\.?\s*(\d{4})", raw)
    if m:
        month_str = m.group(1)[:3].lower()
        year = m.group(2)
        month = _MONTH_MAP.get(month_str)
        if month:
            return f"{year}-{month}"

    return raw


def _is_bullet_line(line: str) -> bool:
    return bool(_BULLET_PATTERN.match(line))


def _is_date_line(line: str) -> bool:
    """Check if a line is primarily a date range or standalone date word."""
    stripped = line.strip()
    if _DATE_RANGE_PATTERN.search(stripped):
        remaining = _DATE_RANGE_PATTERN.sub("", stripped).strip()
        remaining = re.sub(r"^[|\-—·,]+|[|\-—·,]+$", "", remaining)
        return len(remaining) < 10
    if _TRAILING_DATE_PATTERN.match(stripped):
        return True
    if _STANDALONE_PRESENT.match(stripped):
        return True
    # A line that's just a date like "March 2025 - Present" on its own
    return bool(_DATE_PATTERN.match(stripped) and len(stripped) < 30)


def _is_long_text(line: str) -> bool:
    """Check if a line is a long text paragraph (likely content, not a header)."""
    return len(line) > 100 and not _is_bullet_line(line)


_CONTINUATION_ENDINGS = re.compile(
    r"\b(?:and|or|with|for|in|to|by|from|of|at|the|a|an|that|which|who|"
    r"into|via|using|including|such|across|between|through|during)\s*$",
    re.IGNORECASE,
)


def _looks_like_continuation(line: str) -> bool:
    """Check if a line looks like a continuation of the previous line (wrapped text)."""
    if not line or _is_bullet_line(line):
        return False
    # URLs are NOT continuations
    if _URL_PATTERN.match(line.strip()):
        return False
    # Standalone dates/present are NOT continuations
    if _STANDALONE_PRESENT.match(line.strip()):
        return False
    if _is_date_line(line):
        return False
    # Starts with lowercase → likely continuation
    if line[0].islower():
        return True
    # Short fragment ending with period (likely end of a wrapped sentence)
    return (
        len(line) < 80
        and line.endswith(".")
        and not _PIPE_TITLE_PATTERN.match(line)
        and not _DATE_RANGE_PATTERN.search(line)
        and not _TRAILING_DATE_PATTERN.match(line)
    )


def _prev_ends_with_continuation_word(prev: str) -> bool:
    """Check if the previous line ends with a word that suggests the next line continues it."""
    return bool(_CONTINUATION_ENDINGS.search(prev.rstrip()))


def _join_wrapped_lines(lines: list[str]) -> list[str]:
    """Join lines that are continuations of the previous line (PDF text wrapping).

    PDF text extraction often wraps long bullets/paragraphs across multiple lines.
    This function joins them back together.
    """
    if not lines:
        return []

    joined: list[str] = []
    for line in lines:
        if not line:
            joined.append("")
            continue

        if joined and joined[-1]:
            prev = joined[-1]
            # Standard continuation detection (lowercase start, short period fragment)
            if _looks_like_continuation(line):
                joined[-1] = prev.rstrip() + " " + line.lstrip()
                continue
            # Context-based: previous line ends with a conjunction/preposition
            # and current line doesn't look like a new entry header
            if (
                _prev_ends_with_continuation_word(prev)
                and not _is_bullet_line(line)
                and not _is_date_line(line)
                and not _STANDALONE_PRESENT.match(line.strip())
                and not _URL_PATTERN.match(line.strip())
            ):
                joined[-1] = prev.rstrip() + " " + line.lstrip()
                continue

        joined.append(line)

    return joined


def parse_resume_text(text: str) -> ProfileDraft:
    """Parse raw resume text into a CanonicalProfile draft."""
    raw_text = text
    text = _clean(text)
    lines = text.split("\n")
    lines = [_clean(line) for line in lines]
    warnings: list[ParserWarning] = []
    confidence: dict[str, float] = {}

    sections = _detect_sections(lines)

    first_section_line = min(sections.values(), key=lambda r: r[0])[0] if sections else len(lines)
    header_lines = lines[:first_section_line]
    owner, contact_warnings = _parse_contact(header_lines)
    warnings.extend(contact_warnings)
    confidence["contact"] = 0.8 if owner.email else 0.4

    experiences: list[Experience] = []
    education_list: list[Education] = []
    skills: list[Skill] = []
    projects: list[Project] = []
    summary_text: str | None = None

    if "experience" in sections:
        start, end = sections["experience"]
        section_lines = lines[start:end]
        experiences, exp_warnings = _parse_experience_section(section_lines, start)
        warnings.extend(exp_warnings)
        confidence["experience"] = 0.7 if experiences else 0.2

    if "education" in sections:
        start, end = sections["education"]
        section_lines = lines[start:end]
        education_list, edu_warnings = _parse_education_section(section_lines, start)
        warnings.extend(edu_warnings)
        confidence["education"] = 0.7 if education_list else 0.2

    if "skills" in sections:
        start, end = sections["skills"]
        section_lines = lines[start:end]
        skills = _parse_skills_section(section_lines)
        confidence["skills"] = 0.8 if skills else 0.3

    if "projects" in sections:
        start, end = sections["projects"]
        section_lines = lines[start:end]
        projects, proj_warnings = _parse_projects_section(section_lines, start)
        warnings.extend(proj_warnings)
        confidence["projects"] = 0.6 if projects else 0.2

    if "summary" in sections:
        start, end = sections["summary"]
        section_text = "\n".join(lines[start:end]).strip()
        section_text_lines = section_text.split("\n")
        if len(section_text_lines) > 1:
            summary_text = "\n".join(section_text_lines[1:]).strip()
        confidence["summary"] = 0.7 if summary_text else 0.2

    from tailortex.schemas.profile import Summary

    profile = CanonicalProfile(
        profile_id="default",
        owner=owner,
        summary=Summary(source_text=summary_text) if summary_text else None,
        experiences=experiences,
        projects=projects,
        education=education_list,
        skills=skills,
    )

    return ProfileDraft(
        profile=profile,
        raw_text=raw_text,
        warnings=warnings,
        confidence=confidence,
    )


def _detect_sections(lines: list[str]) -> dict[str, tuple[int, int]]:
    """Find section boundaries by matching heading patterns."""
    found: list[tuple[str, int]] = []

    for i, line in enumerate(lines):
        stripped = line.strip().rstrip(":")
        stripped = stripped.strip("-=_")
        if not stripped or len(stripped) > 60:
            continue
        for section_name, pattern in _SECTION_PATTERNS.items():
            if pattern.match(stripped):
                found.append((section_name, i))
                break

    sections: dict[str, tuple[int, int]] = {}
    for idx, (name, start) in enumerate(found):
        end = found[idx + 1][1] if idx + 1 < len(found) else len(lines)
        sections[name] = (start, end)

    return sections


def _parse_contact(header_lines: list[str]) -> tuple[Owner, list[ParserWarning]]:
    """Extract contact info from header lines."""
    warnings: list[ParserWarning] = []
    header_text = "\n".join(header_lines)

    name = ""
    for line in header_lines:
        stripped = line.strip()
        if (
            stripped
            and not _EMAIL_PATTERN.search(stripped)
            and not _URL_PATTERN.search(stripped)
            and not _PHONE_PATTERN.match(stripped)
            and len(stripped) > 2
        ):
            name = stripped
            break

    if not name:
        warnings.append(
            ParserWarning(section="contact", message="Could not detect candidate name.")
        )

    email_match = _EMAIL_PATTERN.search(header_text)
    email = email_match.group(0) if email_match else None

    phone_match = _PHONE_PATTERN.search(header_text)
    phone = phone_match.group(0) if phone_match else None

    links: list[Link] = []
    for url_match in _URL_PATTERN.finditer(header_text):
        url = url_match.group(0)
        label = (
            "GitHub"
            if "github" in url.lower()
            else "LinkedIn"
            if "linkedin" in url.lower()
            else "Website"
        )
        links.append(Link(label=label, url=url))

    location = None
    loc_pattern = re.compile(r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),?\s*([A-Z]{2})\b")
    for line in header_lines:
        loc_match = loc_pattern.search(line)
        if loc_match and loc_match.group(0) != name:
            location = loc_match.group(0)
            break

    owner = Owner(
        full_name=name or "Unknown",
        email=email,
        phone=phone,
        location=location,
        links=links,
    )
    return owner, warnings


def _parse_experience_section(
    lines: list[str], offset: int
) -> tuple[list[Experience], list[ParserWarning]]:
    """Parse experience entries from section lines."""
    warnings: list[ParserWarning] = []

    content_lines: list[str] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            content_lines.append("")
            continue
        if i == 0 and _SECTION_PATTERNS["experience"].match(stripped.rstrip(":")):
            continue
        content_lines.append(stripped)

    content_lines = _join_wrapped_lines(content_lines)

    raw_entries = _split_into_entries(content_lines)

    experiences: list[Experience] = []
    for entry_lines in raw_entries:
        exp = _parse_single_experience(entry_lines, offset)
        if exp:
            experiences.append(exp)

    if not experiences:
        warnings.append(
            ParserWarning(section="experience", message="No experience entries detected.")
        )

    return experiences, warnings


def _is_header_like(line: str) -> bool:
    """Check if a line looks like a header (short, non-bullet, non-long-text)."""
    if not line:
        return False
    return not _is_bullet_line(line) and not _is_long_text(line) and len(line) < 120


def _split_into_entries(lines: list[str]) -> list[list[str]]:
    """Split section lines into individual entry groups.

    Uses a state machine: after seeing content (bullets/long text), a sequence
    of header-like lines signals a new entry boundary.
    """
    entries: list[list[str]] = []
    current: list[str] = []
    seen_content = False

    for i, line in enumerate(lines):
        if not line:
            continue

        is_bullet = _is_bullet_line(line)
        is_long = _is_long_text(line)
        has_date_range = bool(_DATE_RANGE_PATTERN.search(line))
        has_trailing_date = bool(_TRAILING_DATE_PATTERN.match(line))
        has_pipe = bool(_PIPE_TITLE_PATTERN.match(line))
        header_like = _is_header_like(line)

        if not current:
            current.append(line)
            seen_content = is_bullet or is_long
            continue

        # Detect new entry boundary: we've seen content, now we hit a header-like line
        if seen_content and header_like and not is_bullet:
            should_split = False

            # Clear signals of a new entry
            if has_pipe or has_date_range or has_trailing_date:
                should_split = True

            if not should_split:
                # Look ahead: check if the next 1-2 non-empty lines form a header cluster
                next_non_empty = []
                for j in range(i + 1, min(i + 4, len(lines))):
                    if lines[j].strip():
                        next_non_empty.append(lines[j])
                        if len(next_non_empty) >= 2:
                            break

                if next_non_empty:
                    next_line = next_non_empty[0]
                    # Next line is a date → new entry
                    if _is_date_line(next_line) or (
                        _is_header_like(next_line) and not _is_bullet_line(next_line)
                    ):
                        should_split = True

            if should_split:
                entries.append(current)
                current = [line]
                seen_content = False
                continue

        current.append(line)
        if is_bullet or is_long:
            seen_content = True

    if current:
        entries.append(current)

    return entries


def _parse_single_experience(entry_lines: list[str], offset: int) -> Experience | None:
    """Parse a single experience entry from its grouped lines."""
    if not entry_lines:
        return None

    title = ""
    org = ""
    location = ""
    start_date = None
    end_date = None
    is_current = False
    bullets: list[Bullet] = []

    header_lines: list[str] = []
    content_lines: list[str] = []

    for line in entry_lines:
        if _is_bullet_line(line) or content_lines or _is_long_text(line):
            content_lines.append(line)
        else:
            header_lines.append(line)

    # Extract date information from headers
    for hline in header_lines:
        dr = _DATE_RANGE_PATTERN.search(hline)
        if dr:
            start_date = _normalize_date(dr.group(1))
            end_raw = dr.group(2)
            if end_raw.lower() in ("present", "current", "now"):
                is_current = True
            else:
                end_date = _normalize_date(end_raw)
            break
        td = _TRAILING_DATE_PATTERN.match(hline)
        if td:
            date_part = td.group(2).strip()
            if date_part.lower() in ("present", "current", "now"):
                is_current = True
            else:
                start_date = _normalize_date(date_part)
            break

    # Check standalone "Present" / date lines
    if not start_date and not is_current:
        for hline in header_lines:
            if _STANDALONE_PRESENT.match(hline):
                is_current = True
                break
            if _is_date_line(hline):
                dr = _DATE_RANGE_PATTERN.search(hline)
                if dr:
                    start_date = _normalize_date(dr.group(1))
                    end_raw = dr.group(2)
                    if end_raw.lower() in ("present", "current", "now"):
                        is_current = True
                    else:
                        end_date = _normalize_date(end_raw)

    # Extract title and org from headers
    non_date_headers: list[str] = []
    for hline in header_lines:
        if _STANDALONE_PRESENT.match(hline) or _is_date_line(hline):
            continue
        clean = _DATE_RANGE_PATTERN.sub("", hline).strip().rstrip("|—-,")
        clean = re.sub(r"\s+(Present|Current|Now)\s*$", "", clean, flags=re.IGNORECASE).strip()
        if clean and len(clean) > 2:
            non_date_headers.append(clean)

    # Check for "Title | Company" format
    for hline in header_lines:
        pipe_m = _PIPE_TITLE_PATTERN.match(hline)
        if pipe_m:
            left = _DATE_RANGE_PATTERN.sub("", pipe_m.group(1)).strip().rstrip("|—-,")
            right = _DATE_RANGE_PATTERN.sub("", pipe_m.group(2)).strip().rstrip("|—-,")
            left = re.sub(r"\s+(Present|Current|Now)\s*$", "", left, flags=re.IGNORECASE).strip()
            right = re.sub(r"\s+(Present|Current|Now)\s*$", "", right, flags=re.IGNORECASE).strip()
            if left and right:
                title = left
                org = right
                break

    if not title and non_date_headers:
        title = non_date_headers[0]
        if len(non_date_headers) > 1:
            org = non_date_headers[1]

    # Try to extract location from org line
    if org:
        loc_m = re.search(r",?\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),?\s*([A-Z]{2})\s*$", org)
        if loc_m:
            location = loc_m.group(0).strip().lstrip(",").strip()
            org_clean = org[: loc_m.start()].strip().rstrip(",")
            if org_clean:
                org = org_clean

    # Extract bullets — both marked and unmarked
    for line in content_lines:
        bm = _BULLET_PATTERN.match(line)
        text = bm.group(1).strip() if bm else line.strip()

        if text and len(text) > 15:
            bullets.append(Bullet(id=_uid("bullet_"), text=text))

    return Experience(
        id=_uid("exp_"),
        organization=org or "Unknown",
        title=title or "Unknown",
        start_date=start_date or "Unknown",
        end_date=end_date,
        is_current=is_current,
        location=location or None,
        source=Source(type="resume_import", line_range=(offset, offset + len(entry_lines))),
        bullets=bullets,
    )


def _parse_education_section(
    lines: list[str], offset: int
) -> tuple[list[Education], list[ParserWarning]]:
    """Parse education entries."""
    warnings: list[ParserWarning] = []
    education: list[Education] = []

    current_text: list[str] = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            if current_text:
                edu = _parse_single_education(current_text)
                if edu:
                    education.append(edu)
                current_text = []
            continue
        if i == 0 and _SECTION_PATTERNS["education"].match(stripped.rstrip(":")):
            continue

        if (
            current_text
            and len(current_text) >= 2
            and (
                _PIPE_TITLE_PATTERN.match(stripped)
                or (_DATE_RANGE_PATTERN.search(stripped) and not _is_bullet_line(stripped))
            )
        ):
            has_degree = any(
                re.search(
                    r"\b(B\.?S|B\.?A|M\.?S|M\.?A|Ph\.?D|Bachelor|Master|Doctor)",
                    text,
                    re.IGNORECASE,
                )
                for text in current_text
            )
            if has_degree:
                edu = _parse_single_education(current_text)
                if edu:
                    education.append(edu)
                current_text = [stripped]
                continue

        current_text.append(stripped)

    if current_text:
        edu = _parse_single_education(current_text)
        if edu:
            education.append(edu)

    if not education:
        warnings.append(
            ParserWarning(section="education", message="No education entries detected.")
        )

    return education, warnings


def _parse_single_education(text_lines: list[str]) -> Education | None:
    if not text_lines:
        return None

    full_text = " ".join(text_lines)

    date_match = _DATE_RANGE_PATTERN.search(full_text)
    start_date = None
    end_date = None
    if date_match:
        start_date = _normalize_date(date_match.group(1))
        end_raw = date_match.group(2)
        if end_raw.lower() not in ("present", "current", "now"):
            end_date = _normalize_date(end_raw)

    degree_patterns = [
        (r"\b(Ph\.?D\.?|Doctor(?:ate)?)\b", "Ph.D."),
        (r"\b(M\.?S\.?|Master(?:'?s)?(?:\s+of\s+Science)?)\b", "M.S."),
        (r"\b(M\.?A\.?|Master(?:'?s)?(?:\s+of\s+Arts)?)\b", "M.A."),
        (r"\b(M\.?B\.?A\.?)\b", "M.B.A."),
        (r"\b(B\.?S\.?|Bachelor(?:'?s)?(?:\s+of\s+Science)?)\b", "B.S."),
        (r"\b(B\.?A\.?|Bachelor(?:'?s)?(?:\s+of\s+Arts)?)\b", "B.A."),
        (r"\b(B\.?Eng\.?|Bachelor(?:'?s)?(?:\s+of\s+Engineering)?)\b", "B.Eng."),
        (r"\b(Associate(?:'?s)?)\b", "Associate"),
    ]

    degree = "Degree"
    for pattern, label in degree_patterns:
        if re.search(pattern, full_text, re.IGNORECASE):
            degree = label
            break

    gpa_match = re.search(r"GPA[:\s]*(\d+\.\d+)", full_text, re.IGNORECASE)
    gpa = gpa_match.group(1) if gpa_match else None

    institution = "Unknown"
    for tl in text_lines:
        clean = _DATE_RANGE_PATTERN.sub("", tl).strip().rstrip("|—-,")
        if re.search(r"\b(University|College|Institute|School|Academy)\b", clean, re.IGNORECASE):
            if "|" in clean:
                parts = clean.split("|")
                for p in parts:
                    if re.search(
                        r"\b(University|College|Institute|School|Academy)\b",
                        p,
                        re.IGNORECASE,
                    ):
                        institution = p.strip()
                        break
            else:
                institution = clean
            break
    if institution == "Unknown":
        institution = _DATE_RANGE_PATTERN.sub("", text_lines[0]).strip().rstrip("|—-,")

    field_of_study = "Unknown"
    field_match = re.search(r"\bin\s+([A-Z][A-Za-z\s&]+?)(?:\s*[-,]|\s*$)", full_text)
    if field_match:
        field_of_study = field_match.group(1).strip()
    elif "—" in full_text:
        dash_match = re.search(r"—\s*(.+?)(?:\s*,|\s*$)", full_text)
        if dash_match:
            field_of_study = dash_match.group(1).strip()

    return Education(
        id=_uid("edu_"),
        institution=institution or "Unknown",
        degree=degree,
        field=field_of_study,
        start_date=start_date,
        end_date=end_date,
        gpa=gpa,
    )


def _parse_skills_section(lines: list[str]) -> list[Skill]:
    """Parse skills from a skills section."""
    skills: list[Skill] = []
    seen: set[str] = set()

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if i == 0 and _SECTION_PATTERNS["skills"].match(stripped.rstrip(":")):
            continue

        category = None
        if ":" in stripped:
            parts = stripped.split(":", 1)
            if len(parts[0].split()) <= 5:
                category = parts[0].strip()
                stripped = parts[1].strip()

        for skill_name in re.split(r"[,|•\u2022/;]+", stripped):
            skill_name = skill_name.strip().strip("-•* ")
            if skill_name and len(skill_name) < 50 and skill_name.lower() not in seen:
                seen.add(skill_name.lower())
                skills.append(Skill(name=skill_name, category=category))

    return skills


def _is_definite_project_header(line: str) -> bool:
    """Check if a line is definitely a project name (has structural markers)."""
    if not line or _is_bullet_line(line) or _is_long_text(line):
        return False
    # Has em-dash or en-dash separator → "ProjectName — Description"
    if re.search(r"\s[—]\s", line):
        return True
    # Has parenthesized content → "ProjectName (Tech1 | Tech2)"
    return bool(re.search(r"\([^)]+\)", line))


def _parse_projects_section(
    lines: list[str], offset: int
) -> tuple[list[Project], list[ParserWarning]]:
    """Parse project entries.

    Detects project headers by looking for lines with dashes, parenthesized
    tech stacks, or multi-word titles. Short lines like tags ("GenAI", "Research")
    are treated as belonging to the preceding project, not as new entries.
    """
    warnings: list[ParserWarning] = []
    projects: list[Project] = []

    content_lines: list[str] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and _SECTION_PATTERNS["projects"].match(stripped.rstrip(":")):
            continue
        content_lines.append(stripped)

    content_lines = _join_wrapped_lines(content_lines)

    # Remove empty lines — they don't reliably indicate entry boundaries in PDFs
    content_lines = [line for line in content_lines if line]

    # Split into entries based on project headers
    entries: list[list[str]] = []
    current: list[str] = []
    seen_content = False

    for i, line in enumerate(content_lines):
        is_bullet = _is_bullet_line(line)
        is_long = _is_long_text(line)
        is_definite = _is_definite_project_header(line)

        if current and is_definite:
            # Definite project header (has — or parens) → always split
            entries.append(current)
            current = [line]
            seen_content = False
            continue

        if (
            seen_content
            and not is_bullet
            and not is_long
            and len(line) < 120
            and line[0:1].isupper()
        ):
            # After content, a capitalized short line → possible new project
            # Check if followed by content (bullets/long text) within next 2 lines
            has_following_content = False
            for j in range(i + 1, min(i + 3, len(content_lines))):
                nl = content_lines[j]
                if _is_bullet_line(nl) or _is_long_text(nl) or len(nl) > 60:
                    has_following_content = True
                    break
            if has_following_content:
                entries.append(current)
                current = [line]
                seen_content = False
                continue

        current.append(line)
        if is_bullet or is_long:
            seen_content = True

    if current:
        entries.append(current)

    for entry_lines in entries:
        proj = _parse_single_project(entry_lines)
        if proj:
            projects.append(proj)

    return projects, warnings


def _parse_single_project(text_lines: list[str]) -> Project | None:
    if not text_lines:
        return None

    name = text_lines[0].strip()
    # Strip URLs from project name line
    name = _URL_PATTERN.sub("", name).strip()
    description = None
    bullets: list[Bullet] = []
    url = None
    proj_skills: list[str] = []

    # Extract tech stack from name: "Name (React, Node.js)" or "Name | React, Node.js"
    # Check paren_match FIRST — pipes inside parens shouldn't trigger pipe_match
    paren_match = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", name)
    pipe_match = re.match(r"^(.+?)\s*\|\s*(.+)$", name)
    dash_match = re.match(r"^(.+?)\s*[—]\s*(.+)$", name)

    if paren_match:
        name = paren_match.group(1).strip()
        tech_part = paren_match.group(2).strip()
        if re.search(r"[,|]", tech_part) or len(tech_part.split()) <= 4:
            proj_skills = [s.strip() for s in re.split(r"[,|;]+", tech_part) if s.strip()]
        else:
            description = tech_part
    elif pipe_match:
        name = pipe_match.group(1).strip()
        tech_part = pipe_match.group(2).strip()
        proj_skills = [s.strip() for s in re.split(r"[,;]+", tech_part) if s.strip()]
    elif dash_match:
        name = dash_match.group(1).strip()
        rest = dash_match.group(2).strip()
        if len(rest) < 60:
            description = rest

    for line in text_lines[1:]:
        url_match = _URL_PATTERN.search(line)
        if url_match:
            url = url_match.group(0)

        bm = _BULLET_PATTERN.match(line)
        if bm:
            text = bm.group(1).strip()
            if text and len(text) > 15:
                bullets.append(Bullet(id=_uid("bullet_"), text=text))
        elif len(line) > 30 and not _is_definite_project_header(line):
            # Long unmarked text — treat as implicit bullet
            # But skip short tag lines
            bullets.append(Bullet(id=_uid("bullet_"), text=line.strip()))

    return Project(
        id=_uid("proj_"),
        name=name,
        description=description,
        url=url,
        skills=proj_skills,
        bullets=bullets,
    )
