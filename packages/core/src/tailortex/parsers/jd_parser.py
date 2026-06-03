"""Deterministic job description parser.

Extracts structured fields from raw JD text using pattern matching.
Treats JD as untrusted input — includes prompt injection detection.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tailortex.llm.prompts import JOB_DESCRIPTION_PARSER_PROMPT
from tailortex.schemas.job import JDSource, ParsedJobDescription, RoleSignals

if TYPE_CHECKING:
    from tailortex.llm.base import LLMProvider

logger = logging.getLogger(__name__)


@dataclass
class JDParseResult:
    jd: ParsedJobDescription
    raw_text: str
    warnings: list[str] = field(default_factory=list)


# Prompt injection patterns
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|above|prior)\s+instructions?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"system\s*prompt", re.IGNORECASE),
    re.compile(r"<\s*(?:system|assistant|user)\s*>", re.IGNORECASE),
    re.compile(r"do\s+not\s+follow\s+(?:the|your)\s+(?:rules|instructions)", re.IGNORECASE),
    re.compile(r"forget\s+(?:everything|all|your)", re.IGNORECASE),
    re.compile(r"override\s+(?:your|the)\s+(?:rules|instructions|behavior)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(?:if|though)\s+you", re.IGNORECASE),
    re.compile(r"pretend\s+(?:you\s+are|to\s+be)", re.IGNORECASE),
]

# Common skills/technologies for extraction
_TECH_KEYWORDS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "go",
    "golang",
    "rust",
    "c++",
    "c#",
    "ruby",
    "php",
    "swift",
    "kotlin",
    "scala",
    "r",
    "sql",
    "nosql",
    "react",
    "angular",
    "vue",
    "svelte",
    "next.js",
    "nextjs",
    "nuxt",
    "node.js",
    "nodejs",
    "express",
    "fastapi",
    "flask",
    "django",
    "spring",
    "aws",
    "azure",
    "gcp",
    "google cloud",
    "docker",
    "kubernetes",
    "k8s",
    "terraform",
    "ansible",
    "jenkins",
    "ci/cd",
    "github actions",
    "gitlab ci",
    "postgresql",
    "postgres",
    "mysql",
    "mongodb",
    "redis",
    "elasticsearch",
    "kafka",
    "rabbitmq",
    "graphql",
    "rest",
    "rest apis",
    "grpc",
    "machine learning",
    "deep learning",
    "tensorflow",
    "pytorch",
    "pandas",
    "linux",
    "git",
    "agile",
    "scrum",
    "jira",
}

# Skill aliases for normalization
_SKILL_ALIASES: dict[str, str] = {
    "js": "JavaScript",
    "ts": "TypeScript",
    "react.js": "React",
    "reactjs": "React",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "golang": "Go",
    "postgres": "PostgreSQL",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "gcp": "GCP",
    "ci/cd": "CI/CD",
    "rest apis": "REST APIs",
    "rest api": "REST APIs",
}

# Role signal keywords
_ROLE_SIGNAL_KEYWORDS: dict[str, list[str]] = {
    "backend": ["backend", "server", "api", "database", "microservice", "distributed"],
    "frontend": ["frontend", "front-end", "ui", "ux", "css", "react", "angular", "vue"],
    "machine_learning": ["machine learning", "ml", "deep learning", "ai", "data science", "model"],
    "qa": ["testing", "qa", "quality", "test automation", "selenium", "pytest"],
    "leadership": ["lead", "manage", "mentor", "senior", "principal", "architect", "director"],
}

# Ordered from highest to lowest — first match wins.
_SENIORITY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("manager", re.compile(r"\b(?:manager|director|head of|vp)\b", re.IGNORECASE)),
    ("lead", re.compile(r"\b(?:lead|principal|architect)\b", re.IGNORECASE)),
    ("senior", re.compile(r"\b(?:senior|sr\.?|staff)\b", re.IGNORECASE)),
    ("mid", re.compile(r"\b(?:mid[- ]level|intermediate)\b", re.IGNORECASE)),
    ("entry", re.compile(r"\b(?:entry[- ]level|junior|associate|new grad)\b", re.IGNORECASE)),
    ("intern", re.compile(r"\bintern(?:ship)?\b", re.IGNORECASE)),
]

_EMPLOYMENT_TYPE_PATTERNS = {
    "Full-time": re.compile(r"\b(?:full[- ]?time)\b", re.IGNORECASE),
    "Part-time": re.compile(r"\b(?:part[- ]?time)\b", re.IGNORECASE),
    "Contract": re.compile(r"\b(?:contract(?:or)?|freelance)\b", re.IGNORECASE),
    "Internship": re.compile(r"\b(?:intern(?:ship)?)\b", re.IGNORECASE),
}


def _uid() -> str:
    return uuid.uuid4().hex[:12]


def normalize_skill(skill: str) -> str:
    """Normalize a skill name using aliases."""
    lower = skill.strip().lower()
    return _SKILL_ALIASES.get(lower, skill.strip())


def parse_jd_text(
    text: str,
    company: str | None = None,
    role_title: str | None = None,
) -> JDParseResult:
    """Parse raw JD text into a ParsedJobDescription.

    Uses deterministic pattern matching — no LLM calls.
    Treats input as untrusted (checks for prompt injection).
    """
    warnings: list[str] = []
    text_lower = text.lower()

    # Detect prompt injection
    injection_flags: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        matches = pattern.findall(text)
        for m in matches:
            injection_flags.append(f"Suspicious pattern detected: '{m}'")

    if injection_flags:
        warnings.append(
            f"Found {len(injection_flags)} potential prompt injection pattern(s). "
            "These will be ignored during tailoring."
        )

    # Extract skills by scanning for known tech keywords
    found_skills: list[str] = []
    for kw in _TECH_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
            found_skills.append(normalize_skill(kw))

    # Deduplicate (case-insensitive)
    seen: set[str] = set()
    unique_skills: list[str] = []
    for s in found_skills:
        if s.lower() not in seen:
            seen.add(s.lower())
            unique_skills.append(s)

    # Separate required vs preferred
    required_skills, preferred_skills = _classify_skills(text, unique_skills)

    # Extract responsibilities
    responsibilities = _extract_responsibilities(text)

    # Compute role signals
    role_signals = _compute_role_signals(text_lower)

    # Detect seniority
    seniority = _detect_seniority(text)

    # Detect employment type
    employment_type = _detect_employment_type(text)

    # Detect location
    location = _detect_location(text)

    # Domain keywords (broader terms)
    domain_keywords = _extract_domain_keywords(text_lower)

    if not company:
        warnings.append("Company name not provided.")
    if not role_title:
        warnings.append("Role title not provided.")

    jd = ParsedJobDescription(
        job_id=f"jd-{_uid()}",
        source=JDSource(type="pasted_text"),
        company=company,
        role_title=role_title,
        location=location,
        employment_type=employment_type,
        seniority=seniority,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        responsibilities=responsibilities,
        domain_keywords=domain_keywords,
        role_signals=role_signals,
        prompt_injection_flags=injection_flags,
    )

    return JDParseResult(jd=jd, raw_text=text, warnings=warnings)


def _classify_skills(text: str, skills: list[str]) -> tuple[list[str], list[str]]:
    """Split skills into required vs preferred based on context."""
    required: list[str] = []
    preferred: list[str] = []

    # Look for "preferred" / "nice to have" / "bonus" sections
    preferred_section = re.search(
        (
            r"(?:preferred|nice[- ]to[- ]have|bonus|desired|plus|optional)"
            r"\s*(?:qualifications?|skills?|experience)?"
        ),
        text,
        re.IGNORECASE,
    )
    preferred_start = preferred_section.start() if preferred_section else len(text)

    for skill in skills:
        # Find where this skill appears
        match = re.search(r"\b" + re.escape(skill.lower()) + r"\b", text.lower())
        if match and match.start() >= preferred_start:
            preferred.append(skill)
        else:
            required.append(skill)

    return required, preferred


def _extract_responsibilities(text: str) -> list[str]:
    """Extract responsibility bullet points."""
    responsibilities: list[str] = []

    # Look for bullet points or numbered lists
    bullet_pattern = re.compile(r"^\s*(?:[•\-\*\u2022\u25E6]|\d+[.)]\s)\s*(.+)", re.MULTILINE)
    for match in bullet_pattern.finditer(text):
        line = match.group(1).strip()
        # Filter out very short or skill-list-like items
        if len(line) > 20 and not all(w.strip() in _TECH_KEYWORDS for w in line.lower().split(",")):
            responsibilities.append(line)

    return responsibilities[:15]  # Cap at 15


def _compute_role_signals(text_lower: str) -> RoleSignals:
    """Compute role signal scores based on keyword frequency."""
    scores: dict[str, float] = {}

    total_keywords = 0
    for signal, keywords in _ROLE_SIGNAL_KEYWORDS.items():
        count = sum(text_lower.count(kw) for kw in keywords)
        scores[signal] = count
        total_keywords += count

    # Normalize to 0-1 range
    if total_keywords > 0:
        for signal in scores:
            scores[signal] = round(min(scores[signal] / max(total_keywords * 0.3, 1), 1.0), 2)

    return RoleSignals(**scores)


def _detect_seniority(text: str) -> str | None:
    """Detect seniority level from JD text."""
    for level, pattern in _SENIORITY_PATTERNS:
        if pattern.search(text):
            return level
    return None


def _detect_employment_type(text: str) -> str | None:
    for emp_type, pattern in _EMPLOYMENT_TYPE_PATTERNS.items():
        if pattern.search(text):
            return emp_type
    return None


def _detect_location(text: str) -> str | None:
    """Try to detect location from JD text."""
    patterns = [
        re.compile(r"(?:location|based in|office)[:\s]+([^\n,]+)", re.IGNORECASE),
        re.compile(r"\b(remote(?:\s*\([^)]+\))?)\b", re.IGNORECASE),
        re.compile(r"\b(hybrid(?:\s*[-]\s*[^\n,]+)?)\b", re.IGNORECASE),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return None


def _extract_domain_keywords(text_lower: str) -> list[str]:
    """Extract domain-specific keywords."""
    domains = [
        "backend",
        "frontend",
        "full stack",
        "devops",
        "cloud",
        "data",
        "microservices",
        "distributed systems",
        "fintech",
        "healthcare",
        "e-commerce",
        "saas",
        "platform",
        "infrastructure",
        "security",
        "mobile",
        "embedded",
        "real-time",
        "streaming",
    ]
    found = [d for d in domains if d in text_lower]
    return found


# ---------------------------------------------------------------------------
# LLM-based JD parser
# ---------------------------------------------------------------------------

_PARSED_JD_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "job_id": {"type": "string"},
        "source": {"type": "string"},
        "company": {"type": ["string", "null"]},
        "role_title": {"type": ["string", "null"]},
        "location": {"type": ["string", "null"]},
        "employment_type": {"type": ["string", "null"]},
        "seniority": {"type": ["string", "null"]},
        "required_skills": {"type": "array", "items": {"type": "string"}},
        "preferred_skills": {"type": "array", "items": {"type": "string"}},
        "responsibilities": {"type": "array", "items": {"type": "string"}},
        "domain_keywords": {"type": "array", "items": {"type": "string"}},
        "role_signals": {
            "type": "object",
            "properties": {
                "backend": {"type": "number"},
                "frontend": {"type": "number"},
                "machine_learning": {"type": "number"},
                "qa": {"type": "number"},
                "leadership": {"type": "number"},
            },
        },
        "prompt_injection_flags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["job_id", "source", "required_skills", "preferred_skills", "responsibilities"],
}


async def parse_jd_with_llm(
    text: str,
    provider: LLMProvider,
    company: str | None = None,
    role_title: str | None = None,
) -> JDParseResult:
    """Parse raw JD text using an LLM, falling back to deterministic parsing.

    Args:
        text: Raw job description text.
        provider: An LLM provider instance with complete_with_retry().
        company: Optional company name to seed the parse.
        role_title: Optional role title to seed the parse.

    Returns:
        JDParseResult with the parsed job description and any warnings.
    """
    prompt = JOB_DESCRIPTION_PARSER_PROMPT.format(
        job_description=text,
        parsed_job_description_schema=json.dumps(_PARSED_JD_SCHEMA, indent=2),
    )

    result = await provider.complete_with_retry(
        prompt=prompt,
        output_schema=_PARSED_JD_SCHEMA,
    )

    from tailortex.llm.base import LLMError, LLMResponse

    if isinstance(result, LLMError):
        logger.warning(
            "LLM JD parse failed (%s), falling back to deterministic parser. Error: %s",
            provider.name,
            result.error,
        )
        fallback = parse_jd_text(text, company=company, role_title=role_title)
        fallback.warnings.insert(
            0, f"LLM parse failed: {result.error}. Used deterministic fallback."
        )
        return fallback

    if not isinstance(result, LLMResponse) or not result.parsed:
        logger.warning("LLM returned empty parse, falling back to deterministic parser.")
        fallback = parse_jd_text(text, company=company, role_title=role_title)
        fallback.warnings.insert(0, "LLM returned empty parse. Used deterministic fallback.")
        return fallback

    try:
        parsed = result.parsed
        if isinstance(parsed, list):
            parsed = parsed[0] if parsed else {}

        # Merge user-supplied company/role_title if LLM didn't return them
        if company and not parsed.get("company"):
            parsed["company"] = company
        if role_title and not parsed.get("role_title"):
            parsed["role_title"] = role_title

        role_signals = parsed.get("role_signals", {})
        if not isinstance(role_signals, dict):
            role_signals = {}

        jd = ParsedJobDescription(
            job_id=parsed.get("job_id", f"jd-{_uid()}"),
            source=JDSource(type=parsed.get("source", "pasted_text")),
            company=parsed.get("company"),
            role_title=parsed.get("role_title"),
            location=parsed.get("location"),
            employment_type=parsed.get("employment_type"),
            seniority=parsed.get("seniority"),
            required_skills=parsed.get("required_skills", []) or [],
            preferred_skills=parsed.get("preferred_skills", []) or [],
            responsibilities=parsed.get("responsibilities", []) or [],
            domain_keywords=parsed.get("domain_keywords", []) or [],
            role_signals=RoleSignals(
                backend=float(role_signals.get("backend", 0)),
                frontend=float(role_signals.get("frontend", 0)),
                machine_learning=float(role_signals.get("machine_learning", 0)),
                qa=float(role_signals.get("qa", 0)),
                leadership=float(role_signals.get("leadership", 0)),
            ),
            prompt_injection_flags=parsed.get("prompt_injection_flags", []) or [],
        )
        return JDParseResult(jd=jd, raw_text=text)
    except Exception as exc:
        logger.warning(
            "Failed to construct ParsedJobDescription from LLM response (%s). "
            "Falling back to deterministic parser. Error: %s",
            provider.name,
            exc,
        )
        fallback = parse_jd_text(text, company=company, role_title=role_title)
        fallback.warnings.insert(
            0, f"LLM response construction failed: {exc}. Used deterministic fallback."
        )
        return fallback
