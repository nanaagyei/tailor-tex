"""Export manager — produces .tex, .md, Overleaf bundles, and reports."""

from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path

from tailortex.rendering.latex_renderer import build_template_context, render_latex
from tailortex.reports.validation_report import generate_validation_report_markdown
from tailortex.schemas.profile import CanonicalProfile
from tailortex.schemas.resume import GeneratedBullet, ResumePlan
from tailortex.schemas.validation import ValidationReport


def export_tex(
    profile: CanonicalProfile,
    plan: ResumePlan,
    output_path: Path,
    generated_bullets: list[GeneratedBullet] | None = None,
    bold_keywords: list[str] | None = None,
    template_dir: Path | None = None,
    template_id: str = "ats-modern",
) -> Path:
    """Export rendered LaTeX to a .tex file."""
    tex = render_latex(
        profile,
        plan,
        generated_bullets,
        bold_keywords,
        template_dir,
        template_id,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(tex, encoding="utf-8")
    return output_path


def export_markdown(
    profile: CanonicalProfile,
    plan: ResumePlan,
    output_path: Path,
    generated_bullets: list[GeneratedBullet] | None = None,
    bold_keywords: list[str] | None = None,
) -> Path:
    """Export a plain Markdown version of the resume."""
    ctx = build_template_context(profile, plan, generated_bullets, bold_keywords, escape=False)

    lines: list[str] = []

    # Heading
    lines.append(f"# {ctx['name']}")

    # Contact line
    contact_parts: list[str] = []
    contact = ctx["contact"]
    if contact.get("email"):
        contact_parts.append(f"[{contact['email']}](mailto:{contact['email']})")
    if contact.get("phone"):
        contact_parts.append(contact["phone"])
    for link in contact.get("links", []):
        contact_parts.append(f"[{link}]({link})")
    if contact.get("location"):
        contact_parts.append(contact["location"])
    if contact_parts:
        lines.append("")
        lines.append(" | ".join(contact_parts))

    # Summary
    if ctx.get("summary"):
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(ctx["summary"])

    # Skills
    if ctx.get("skills"):
        lines.append("")
        lines.append("## Skills")
        lines.append("")
        for group in ctx["skills"]:
            items = ", ".join(group["items"])
            lines.append(f"- **{group['group']}**: {items}")

    # Experience
    if ctx.get("experience"):
        lines.append("")
        lines.append("## Experience")
        for exp in ctx["experience"]:
            lines.append("")
            location_str = f", {exp['location']}" if exp.get("location") else ""
            lines.append(
                f"### {exp['title']} — {exp['organization']}{location_str}"
            )
            lines.append("")
            lines.append(exp["dates"])
            if exp.get("bullets"):
                lines.append("")
                for bullet in exp["bullets"]:
                    lines.append(f"- {bullet}")

    # Projects
    if ctx.get("projects"):
        lines.append("")
        lines.append("## Projects")
        for proj in ctx["projects"]:
            lines.append("")
            skill_str = ""
            if proj.get("skills"):
                skill_str = f" ({', '.join(proj['skills'])})"
            lines.append(f"### {proj['name']}{skill_str}")
            if proj.get("description"):
                lines.append("")
                lines.append(proj["description"])
            if proj.get("bullets"):
                lines.append("")
                for bullet in proj["bullets"]:
                    lines.append(f"- {bullet}")

    # Education
    if ctx.get("education"):
        lines.append("")
        lines.append("## Education")
        for edu in ctx["education"]:
            lines.append("")
            degree_str = edu["degree"]
            if edu.get("field"):
                degree_str += f" in {edu['field']}"
            lines.append(f"### {edu['institution']}")
            lines.append("")
            lines.append(f"{degree_str} — {edu['dates']}")

    # Certifications
    if ctx.get("certifications"):
        lines.append("")
        lines.append("## Certifications")
        for cert in ctx["certifications"]:
            lines.append("")
            issuer_str = f" — {cert['issuer']}" if cert.get("issuer") else ""
            date_str = f" ({cert['date']})" if cert.get("date") else ""
            lines.append(f"- **{cert['name']}**{issuer_str}{date_str}")

    # Publications
    if ctx.get("publications"):
        lines.append("")
        lines.append("## Selected Publications")
        for pub in ctx["publications"]:
            lines.append("")
            venue_str = f" {pub['venue']}" if pub.get("venue") else ""
            date_str = f", {pub['date']}" if pub.get("date") else ""
            lines.append(f"- **\"{pub['title']}\"**{venue_str}{date_str}")
            if pub.get("url"):
                lines.append(f"  {pub['url']}")

    # Awards
    if ctx.get("awards"):
        lines.append("")
        lines.append("## Honors & Awards")
        for award in ctx["awards"]:
            lines.append("")
            issuer_str = f", {award['issuer']}" if award.get("issuer") else ""
            date_str = f" — {award['date']}" if award.get("date") else ""
            lines.append(f"- **{award['title']}**{issuer_str}{date_str}")

    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def export_overleaf_bundle(
    profile: CanonicalProfile,
    plan: ResumePlan,
    output_path: Path,
    generated_bullets: list[GeneratedBullet] | None = None,
    bold_keywords: list[str] | None = None,
    template_dir: Path | None = None,
    template_id: str = "ats-modern",
) -> Path:
    """Export a zip bundle suitable for Overleaf upload.

    Contains main.tex and a README. No private metadata.
    """
    tex = render_latex(
        profile,
        plan,
        generated_bullets,
        bold_keywords,
        template_dir,
        template_id,
    )

    readme = (
        "# TailorTex Resume\n\n"
        "Upload this zip to Overleaf or compile locally with:\n\n"
        "    tectonic main.tex\n"
        "    # or\n"
        "    latexmk -pdf main.tex\n"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("main.tex", tex)
        zf.writestr("README.md", readme)

    return output_path


def export_validation_report(
    report: ValidationReport,
    output_path: Path,
) -> Path:
    """Export validation report as Markdown."""
    markdown = generate_validation_report_markdown(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def export_diff_report(
    original_bullets: list[str],
    generated_bullets: list[GeneratedBullet],
    output_path: Path,
) -> Path:
    """Export a diff report showing original vs generated text."""
    lines: list[str] = []
    lines.append("# Diff Report\n")

    gen_map: dict[str, GeneratedBullet] = {}
    for gb in generated_bullets:
        for sid in gb.source_bullet_ids:
            gen_map[sid] = gb

    for i, orig in enumerate(original_bullets):
        lines.append(f"## Bullet {i + 1}\n")
        lines.append(f"**Original:** {orig}")
        lines.append("")

    if generated_bullets:
        lines.append("## Generated Bullets\n")
        for gb in generated_bullets:
            status_icon = {"supported": "+", "needs_confirmation": "?", "rejected": "x"}
            icon = status_icon.get(gb.validation_status, "?")
            lines.append(f"- [{icon}] {gb.text}")
            if gb.validation_notes:
                for note in gb.validation_notes:
                    lines.append(f"  - Note: {note}")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def compile_pdf(
    tex_path: Path,
    output_dir: Path | None = None,
) -> Path | None:
    """Attempt to compile .tex to PDF using available engine.

    Returns the PDF path on success, None if no engine is available.
    """
    out = output_dir or tex_path.parent

    for engine_cmd in ["tectonic", "latexmk"]:
        if shutil.which(engine_cmd) is None:
            continue

        if engine_cmd == "tectonic":
            cmd = ["tectonic", str(tex_path), "--outdir", str(out)]
        else:
            cmd = ["latexmk", "-pdf", f"-outdir={out}", str(tex_path)]

        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=120,
            )
            pdf_name = tex_path.stem + ".pdf"
            pdf_path = out / pdf_name
            if pdf_path.exists():
                return pdf_path
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            continue

    return None
