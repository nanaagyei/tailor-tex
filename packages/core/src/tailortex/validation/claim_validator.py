"""Claim validator — cross-references generated claims against evidence.

Statuses:
  - supported: evidence directly supports the claim
  - needs_confirmation: claim may be true but needs user-supplied detail
  - rejected: claim adds fabricated content not in evidence
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from tailortex.schemas.profile import CanonicalProfile
from tailortex.schemas.resume import GeneratedBullet
from tailortex.schemas.validation import ClaimResult, ValidationReport, ValidationSummary, Warning


def validate_claims(
    generated_bullets: list[GeneratedBullet],
    profile: CanonicalProfile,
) -> ValidationReport:
    """Validate all generated bullets against the canonical profile.

    Uses deterministic checks — no LLM required.
    """
    claim_results: list[ClaimResult] = []
    warnings: list[Warning] = []

    evidence = _build_evidence_index(profile)

    for bullet in generated_bullets:
        original_text = _find_original_text(bullet, profile)
        result = _validate_single_claim(bullet, original_text, evidence)
        claim_results.append(result)

        if result.status == "rejected":
            warnings.append(Warning(
                type="REJECTED_CLAIM",
                message=f"Claim rejected for bullet {bullet.id}: {result.claim}",
            ))

    supported = sum(1 for r in claim_results if r.status == "supported")
    needs_confirm = sum(1 for r in claim_results if r.status == "needs_confirmation")
    rejected = sum(1 for r in claim_results if r.status == "rejected")

    if rejected > 0:
        status = "failed"
    elif needs_confirm > 0:
        status = "passed_with_warnings"
    else:
        status = "passed"

    summary = ValidationSummary(
        supported_claims=supported,
        needs_confirmation=needs_confirm,
        rejected_claims=rejected,
        warnings=len(warnings),
    )

    return ValidationReport(
        resume_id="validation",
        status=status,
        claims=claim_results,
        summary=summary,
        warnings=warnings,
    )


@dataclass
class _EvidenceIndex:
    """Pre-computed index of approved evidence for fast lookup."""

    all_skills: set[str]
    all_companies: set[str]
    all_titles: set[str]
    all_metrics: set[str]
    all_bullet_text: set[str]
    all_tools: set[str]
    all_institutions: set[str]
    all_degrees: set[str]


def _build_evidence_index(profile: CanonicalProfile) -> _EvidenceIndex:
    """Build a searchable index from the approved profile."""
    skills: set[str] = set()
    companies: set[str] = set()
    titles: set[str] = set()
    metrics: set[str] = set()
    bullet_text: set[str] = set()
    tools: set[str] = set()
    institutions: set[str] = set()
    degrees: set[str] = set()

    for skill in profile.skills:
        skills.add(skill.name.lower())

    for exp in profile.experiences:
        companies.add(exp.organization.lower())
        titles.add(exp.title.lower())
        for b in exp.bullets:
            bullet_text.add(b.text.lower())
            for s in b.skills:
                skills.add(s.lower())
                tools.add(s.lower())
            for m in b.metrics:
                metrics.add(m.lower())

    for proj in profile.projects:
        for s in proj.skills:
            skills.add(s.lower())
            tools.add(s.lower())
        for b in proj.bullets:
            bullet_text.add(b.text.lower())
            for s in b.skills:
                skills.add(s.lower())
                tools.add(s.lower())
            for m in b.metrics:
                metrics.add(m.lower())

    for edu in profile.education:
        institutions.add(edu.institution.lower())
        if edu.degree:
            degrees.add(edu.degree.lower())

    return _EvidenceIndex(
        all_skills=skills,
        all_companies=companies,
        all_titles=titles,
        all_metrics=metrics,
        all_bullet_text=bullet_text,
        all_tools=tools,
        all_institutions=institutions,
        all_degrees=degrees,
    )


def _find_original_text(
    bullet: GeneratedBullet,
    profile: CanonicalProfile,
) -> str:
    """Find the original bullet text from source_bullet_ids."""
    for source_id in bullet.source_bullet_ids:
        for exp in profile.experiences:
            for b in exp.bullets:
                if b.id == source_id:
                    return b.text
        for proj in profile.projects:
            for b in proj.bullets:
                if b.id == source_id:
                    return b.text
    return ""


def _validate_single_claim(
    bullet: GeneratedBullet,
    original_text: str,
    evidence: _EvidenceIndex,
) -> ClaimResult:
    """Validate a single generated bullet against evidence."""
    rewritten = bullet.text.lower()
    original = original_text.lower()

    # Check 1: If text is unchanged, it's supported
    if bullet.text.strip() == original_text.strip():
        return ClaimResult(
            claim=bullet.text,
            status="supported",
            evidence_ids=bullet.source_bullet_ids,
        )

    # Check 2: Fabricated metrics
    fabricated_metrics = _detect_fabricated_metrics(rewritten, original, evidence)
    if fabricated_metrics:
        return ClaimResult(
            claim=f"Fabricated metric(s): {', '.join(fabricated_metrics)}",
            status="rejected",
        )

    # Check 3: Fabricated tools/skills
    fabricated_tools = _detect_fabricated_tools(rewritten, original, evidence)
    if fabricated_tools:
        return ClaimResult(
            claim=f"Tool(s) not in evidence: {', '.join(fabricated_tools)}",
            status="rejected",
        )

    # Check 4: Scope inflation (leadership claims)
    if _detect_scope_inflation(rewritten, original, evidence):
        return ClaimResult(
            claim="Leadership or scope claim not supported by evidence.",
            status="rejected",
        )

    # Check 5: If significant changes, mark as needs_confirmation
    if _significant_changes(rewritten, original):
        return ClaimResult(
            claim=bullet.text,
            status="needs_confirmation",
        )

    return ClaimResult(
        claim=bullet.text,
        status="supported",
        evidence_ids=bullet.source_bullet_ids,
    )


def _detect_fabricated_metrics(
    rewritten: str,
    original: str,
    evidence: _EvidenceIndex,
) -> list[str]:
    """Detect numeric metrics in rewritten text not present in evidence."""
    fabricated: list[str] = []

    metric_patterns = [
        re.compile(r"\b\d+(?:\.\d+)?%\b"),
        re.compile(r"\b\d+(?:\.\d+)?x\b"),
        re.compile(r"\$\d+(?:,\d{3})*(?:\.\d+)?"),
        re.compile(r"\b\d{2,}(?:,\d{3})*\+?\b"),
    ]

    for pattern in metric_patterns:
        for match in pattern.finditer(rewritten):
            metric = match.group()
            if metric not in original and metric.lower() not in evidence.all_metrics:
                if not any(metric in m for m in evidence.all_metrics):
                    fabricated.append(metric)

    return fabricated


def _detect_fabricated_tools(
    rewritten: str,
    original: str,
    evidence: _EvidenceIndex,
) -> list[str]:
    """Detect tool/technology names added that aren't in evidence."""
    common_tools = {
        "kubernetes", "k8s", "terraform", "ansible", "jenkins", "kafka",
        "rabbitmq", "elasticsearch", "mongodb", "cassandra", "dynamodb",
        "graphql", "grpc", "spark", "hadoop", "airflow", "mlflow",
        "pytorch", "tensorflow", "scikit-learn", "pandas", "numpy",
    }

    fabricated: list[str] = []
    for tool in common_tools:
        if tool in rewritten and tool not in original and tool not in evidence.all_tools:
            fabricated.append(tool)

    return fabricated


def _detect_scope_inflation(
    rewritten: str,
    original: str,
    evidence: _EvidenceIndex,
) -> bool:
    """Detect leadership/scope claims not in evidence."""
    leadership_terms = [
        "led a team", "managed a team", "directed",
        "oversaw", "spearheaded", "headed",
        "team of", "reports",
    ]

    for term in leadership_terms:
        if term in rewritten and term not in original:
            has_leadership_evidence = any(
                term in bt for bt in evidence.all_bullet_text
            )
            if not has_leadership_evidence:
                return True

    return False


def _significant_changes(rewritten: str, original: str) -> bool:
    """Detect if the rewritten text differs significantly from original."""
    original_words = set(original.split())
    rewritten_words = set(rewritten.split())

    if not original_words:
        return True

    intersection = original_words & rewritten_words
    union = original_words | rewritten_words
    similarity = len(intersection) / max(len(union), 1)

    return similarity < 0.5
