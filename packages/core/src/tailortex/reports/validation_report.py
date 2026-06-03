"""Validation report generation — produces Markdown reports from claim validation results."""

from __future__ import annotations

from tailortex.schemas.validation import ValidationReport


def generate_validation_report_markdown(
    report: ValidationReport,
    profile_name: str | None = None,
) -> str:
    """Generate a nicely formatted Markdown validation report.

    Args:
        report: The validation report with claims and warnings.
        profile_name: Optional profile name to include in the report header.

    Returns:
        A Markdown-formatted string.
    """
    lines: list[str] = []

    lines.append("# Validation Report")
    lines.append("")

    if profile_name:
        lines.append(f"**Profile:** {profile_name}")
        lines.append("")

    lines.append(f"**Status:** {report.status}")
    lines.append("")

    lines.append("## Summary")
    lines.append("")

    lines.append("| Category | Count |")
    lines.append("|----------|-------|")
    lines.append(f"| Supported | {report.summary.supported_claims} |")
    lines.append(f"| Needs Confirmation | {report.summary.needs_confirmation} |")
    lines.append(f"| Rejected | {report.summary.rejected_claims} |")
    lines.append(f"| Warnings | {report.summary.warnings} |")
    lines.append("")

    if report.claims:
        lines.append("## Claims")
        lines.append("")

        status_badges = {
            "supported": "✅ Supported",
            "needs_confirmation": "⚠️ Needs Confirmation",
            "rejected": "❌ Rejected",
        }

        lines.append("| Status | Claim |")
        lines.append("|--------|-------|")
        for claim in report.claims:
            badge = status_badges.get(claim.status, "❓ Unknown")
            lines.append(f"| {badge} | {claim.claim} |")
        lines.append("")

    if report.warnings:
        lines.append("## Warnings")
        lines.append("")
        for w in report.warnings:
            lines.append(f"- **{w.type}**: {w.message}")
        lines.append("")

    return "\n".join(lines)
