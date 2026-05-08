"""Evidence scoring engine.

Scores profile items against a parsed job description using a weighted
hybrid approach:
  35% skill overlap + 25% responsibility + 15% recency + 15% role signal + 10% evidence strength
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from tailortex.schemas.job import ParsedJobDescription
from tailortex.schemas.profile import CanonicalProfile, Experience, Project

# Skill aliases for matching
_ALIASES: dict[str, set[str]] = {
    "javascript": {"js", "javascript", "ecmascript"},
    "typescript": {"ts", "typescript"},
    "react": {"react", "react.js", "reactjs"},
    "node.js": {"node", "node.js", "nodejs"},
    "next.js": {"next", "next.js", "nextjs"},
    "postgresql": {"postgresql", "postgres", "psql"},
    "kubernetes": {"kubernetes", "k8s"},
    "ci/cd": {"ci/cd", "ci cd", "continuous integration", "continuous deployment"},
    "rest apis": {"rest", "rest api", "rest apis", "restful"},
    "go": {"go", "golang"},
    "python": {"python", "py"},
    "docker": {"docker", "containerization"},
    "aws": {"aws", "amazon web services"},
    "gcp": {"gcp", "google cloud", "google cloud platform"},
}

# Build reverse lookup
_ALIAS_LOOKUP: dict[str, str] = {}
for canonical, aliases in _ALIASES.items():
    for alias in aliases:
        _ALIAS_LOOKUP[alias] = canonical


def _normalize(skill: str) -> str:
    lower = skill.strip().lower()
    return _ALIAS_LOOKUP.get(lower, lower)


@dataclass
class MatchScore:
    item_id: str
    item_type: str  # "experience" or "project"
    total_score: float
    skill_score: float
    responsibility_score: float
    recency_score: float
    role_signal_score: float
    evidence_score: float
    matched_skills: list[str]


def score_experience(
    exp: Experience,
    jd: ParsedJobDescription,
    now: datetime | None = None,
) -> MatchScore:
    """Score an experience entry against a job description."""
    now = now or datetime.now()

    all_jd_skills = set(_normalize(s) for s in jd.required_skills + jd.preferred_skills)
    exp_skills = set()
    for bullet in exp.bullets:
        for s in bullet.skills:
            exp_skills.add(_normalize(s))

    # Skill overlap
    overlap = all_jd_skills & exp_skills
    skill_score = len(overlap) / max(len(all_jd_skills), 1)
    matched_skills = [
        s for s in jd.required_skills + jd.preferred_skills if _normalize(s) in overlap
    ]

    # Responsibility overlap (keyword matching)
    resp_score = _responsibility_overlap(exp, jd)

    # Recency
    recency = _recency_score(exp.start_date, exp.is_current, now)

    # Role signal
    role_signal = _role_signal_score(exp, jd)

    # Evidence strength (approved bullets with metrics score higher)
    evidence = _evidence_strength(exp)

    total = (
        0.35 * skill_score
        + 0.25 * resp_score
        + 0.15 * recency
        + 0.15 * role_signal
        + 0.10 * evidence
    )

    return MatchScore(
        item_id=exp.id,
        item_type="experience",
        total_score=round(total, 4),
        skill_score=round(skill_score, 4),
        responsibility_score=round(resp_score, 4),
        recency_score=round(recency, 4),
        role_signal_score=round(role_signal, 4),
        evidence_score=round(evidence, 4),
        matched_skills=matched_skills,
    )


def score_project(
    project: Project,
    jd: ParsedJobDescription,
) -> MatchScore:
    """Score a project against a job description."""
    all_jd_skills = set(_normalize(s) for s in jd.required_skills + jd.preferred_skills)

    proj_skills = set(_normalize(s) for s in project.skills)
    for bullet in project.bullets:
        for s in bullet.skills:
            proj_skills.add(_normalize(s))

    overlap = all_jd_skills & proj_skills
    skill_score = len(overlap) / max(len(all_jd_skills), 1)
    matched_skills = [
        s for s in jd.required_skills + jd.preferred_skills if _normalize(s) in overlap
    ]

    # Projects get lower recency and role signal scores
    total = 0.35 * skill_score + 0.25 * 0.0 + 0.15 * 0.3 + 0.15 * 0.0 + 0.10 * 0.5

    return MatchScore(
        item_id=project.id,
        item_type="project",
        total_score=round(total, 4),
        skill_score=round(skill_score, 4),
        responsibility_score=0.0,
        recency_score=0.3,
        role_signal_score=0.0,
        evidence_score=0.5,
        matched_skills=matched_skills,
    )


def score_profile(
    profile: CanonicalProfile,
    jd: ParsedJobDescription,
) -> list[MatchScore]:
    """Score all experiences and projects in a profile against a JD.

    Returns scores sorted by total_score descending.
    """
    scores: list[MatchScore] = []
    for exp in profile.experiences:
        scores.append(score_experience(exp, jd))
    for proj in profile.projects:
        scores.append(score_project(proj, jd))
    scores.sort(key=lambda s: s.total_score, reverse=True)
    return scores


def _responsibility_overlap(exp: Experience, jd: ParsedJobDescription) -> float:
    """Score how well experience bullets match JD responsibilities."""
    if not jd.responsibilities:
        return 0.0

    exp_text = " ".join(b.text.lower() for b in exp.bullets)
    matches = 0

    for resp in jd.responsibilities:
        # Extract significant words from responsibility
        words = set(re.findall(r"\b[a-z]{4,}\b", resp.lower()))
        if words:
            word_matches = sum(1 for w in words if w in exp_text)
            if word_matches / len(words) >= 0.3:
                matches += 1

    return matches / len(jd.responsibilities)


def _recency_score(start_date: str, is_current: bool, now: datetime) -> float:
    """Score based on how recent the experience is."""
    if is_current:
        return 1.0

    try:
        parts = start_date.split("-")
        year = int(parts[0])
        years_ago = now.year - year
        if years_ago <= 1:
            return 0.9
        elif years_ago <= 3:
            return 0.7
        elif years_ago <= 5:
            return 0.5
        else:
            return 0.3
    except (ValueError, IndexError):
        return 0.3


def _role_signal_score(exp: Experience, jd: ParsedJobDescription) -> float:
    """Score how well experience aligns with role signals."""
    exp_text = " ".join(b.text.lower() for b in exp.bullets)

    from tailortex.parsers.jd_parser import _ROLE_SIGNAL_KEYWORDS

    # Find dominant JD signals
    signals = jd.role_signals
    signal_dict = {
        "backend": signals.backend,
        "frontend": signals.frontend,
        "machine_learning": signals.machine_learning,
        "qa": signals.qa,
        "leadership": signals.leadership,
    }

    score = 0.0
    total_weight = 0.0

    for signal, weight in signal_dict.items():
        if weight > 0:
            keywords = _ROLE_SIGNAL_KEYWORDS.get(signal, [])
            match_count = sum(1 for kw in keywords if kw in exp_text)
            signal_score = min(match_count / max(len(keywords), 1), 1.0)
            score += weight * signal_score
            total_weight += weight

    return score / max(total_weight, 1.0)


def _evidence_strength(exp: Experience) -> float:
    """Score evidence quality — approved bullets with metrics rank higher."""
    if not exp.bullets:
        return 0.0

    total = 0.0
    for bullet in exp.bullets:
        base = 0.5
        if bullet.approved:
            base += 0.25
        if bullet.metrics:
            base += 0.25
        total += base

    return total / len(exp.bullets)
