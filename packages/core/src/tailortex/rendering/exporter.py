"""Export manager — produces .tex files, Overleaf bundles, and reports."""

from __future__ import annotations

import shutil
import subprocess
import zipfile
from io import BytesIO
from pathlib import Path

from tailortex.schemas.profile import CanonicalProfile
from tailortex.schemas.resume import GeneratedBullet, ResumePlan
from tailortex.schemas.validation import ValidationReport
from tailortex.rendering.latex_renderer import render_latex


def export_tex(
    profile: CanonicalProfile,
    plan: ResumePlan,
    output_path: Path,
    generated_bullets: list[GeneratedBullet] | None = None,
    bold_keywords: list[str] | None = None,
    template_dir: Path | None = None,
) -> Path:
    """Export rendered LaTeX to a .tex file."""
    tex = render_latex(
        profile, plan, generated_bullets, bold_keywords, template_dir,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(tex, encoding="utf-8")
    return output_path


def export_overleaf_bundle(
    profile: CanonicalProfile,
    plan: ResumePlan,
    output_path: Path,
    generated_bullets: list[GeneratedBullet] | None = None,
    bold_keywords: list[str] | None = None,
    template_dir: Path | None = None,
) -> Path:
    """Export a zip bundle suitable for Overleaf upload.

    Contains main.tex and a README. No private metadata.
    """
    tex = render_latex(
        profile, plan, generated_bullets, bold_keywords, template_dir,
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
    lines: list[str] = []
    lines.append("# Validation Report\n")
    lines.append(f"**Status:** {report.status}\n")
    lines.append("## Summary\n")
    lines.append(f"- Supported: {report.summary.supported_claims}")
    lines.append(f"- Needs confirmation: {report.summary.needs_confirmation}")
    lines.append(f"- Rejected: {report.summary.rejected_claims}")
    lines.append(f"- Warnings: {report.summary.warnings}")
    lines.append("")

    if report.claims:
        lines.append("## Claims\n")
        for claim in report.claims:
            icon = {"supported": "+", "needs_confirmation": "?", "rejected": "x"}
            lines.append(f"- [{icon.get(claim.status, '?')}] {claim.claim}")
        lines.append("")

    if report.warnings:
        lines.append("## Warnings\n")
        for w in report.warnings:
            lines.append(f"- **{w.type}**: {w.message}")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
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
