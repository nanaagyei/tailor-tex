"""LaTeX renderer — converts profile + resume plan into .tex output.

Uses Jinja2 templates with LaTeX escaping.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from tailortex.schemas.profile import CanonicalProfile
from tailortex.schemas.resume import GeneratedBullet, ResumePlan

# LaTeX special characters handled in escape_latex().

# Default template directory (sibling packages/templates).
_DEFAULT_TEMPLATE_DIR = Path(__file__).resolve().parents[4] / "templates"


def escape_latex(text: str) -> str:
    """Escape LaTeX special characters in user-generated content."""
    # Process character by character to avoid double-escaping.
    result: list[str] = []
    for ch in text:
        if ch == "\\":
            result.append(r"\textbackslash{}")
        elif ch == "~":
            result.append(r"\textasciitilde{}")
        elif ch == "^":
            result.append(r"\textasciicircum{}")
        elif ch in "&%$#_{}":
            result.append(f"\\{ch}")
        else:
            result.append(ch)
    return "".join(result)


def _bold_keywords(text: str, keywords: list[str]) -> str:
    """Bold approved keywords in a bullet (max 3 per bullet)."""
    bolded = 0
    for kw in keywords:
        if bolded >= 3:
            break
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        if pattern.search(text):
            text = pattern.sub(rf"\\textbf{{{kw}}}", text, count=1)
            bolded += 1
    return text


def build_template_context(
    profile: CanonicalProfile,
    plan: ResumePlan,
    generated_bullets: list[GeneratedBullet] | None = None,
    bold_keywords: list[str] | None = None,
) -> dict[str, Any]:
    """Build the template context dict from profile + plan."""
    esc = escape_latex
    bk = bold_keywords or []

    # Build bullet lookup: source_id -> generated text
    bullet_map: dict[str, str] = {}
    if generated_bullets:
        for gb in generated_bullets:
            # Only include supported or needs_confirmation bullets
            if gb.validation_status != "rejected":
                for sid in gb.source_bullet_ids:
                    bullet_map[sid] = gb.text

    # Contact
    contact: dict[str, Any] = {
        "email": esc(profile.owner.email or ""),
        "phone": esc(profile.owner.phone or ""),
        "location": esc(profile.owner.location or ""),
        "links": [esc(link.url) for link in (profile.owner.links or [])],
    }

    # Skills — group by category or flatten
    skill_groups: list[dict[str, Any]] = []
    categorized: dict[str, list[str]] = {}
    for skill in profile.skills:
        cat = skill.category or "Technical"
        categorized.setdefault(cat, []).append(esc(skill.name))
    for group_name, items in categorized.items():
        skill_groups.append({"group": esc(group_name), "items": items})

    # Experience
    experience_list: list[dict[str, Any]] = []
    for exp in profile.experiences:
        exp_bullets: list[str] = []
        for b in exp.bullets:
            text = bullet_map.get(b.id, b.text)
            text = esc(text)
            if bk:
                text = _bold_keywords(text, bk)
            exp_bullets.append(text)

        dates = exp.start_date or ""
        if exp.end_date:
            dates += f" -- {exp.end_date}"
        elif exp.is_current:
            dates += " -- Present"

        experience_list.append(
            {
                "title": esc(exp.title),
                "organization": esc(exp.organization),
                "location": esc(exp.location or ""),
                "dates": esc(dates),
                "bullets": exp_bullets,
            }
        )

    # Projects
    project_list: list[dict[str, Any]] = []
    for proj in profile.projects:
        proj_bullets: list[str] = []
        for b in proj.bullets:
            text = bullet_map.get(b.id, b.text)
            text = esc(text)
            if bk:
                text = _bold_keywords(text, bk)
            proj_bullets.append(text)

        project_list.append(
            {
                "name": esc(proj.name),
                "description": esc(proj.description or ""),
                "skills": [esc(s) for s in proj.skills],
                "bullets": proj_bullets,
            }
        )

    # Education
    education_list: list[dict[str, Any]] = []
    for edu in profile.education:
        dates = edu.start_date or ""
        if edu.end_date:
            dates += f" -- {edu.end_date}"

        education_list.append(
            {
                "institution": esc(edu.institution),
                "degree": esc(edu.degree or ""),
                "field": esc(edu.field or ""),
                "dates": esc(dates),
            }
        )

    # Certifications
    cert_list: list[dict[str, Any]] = []
    for cert in profile.certifications:
        cert_list.append(
            {
                "name": esc(cert.name),
                "issuer": esc(cert.issuer or ""),
                "date": esc(cert.date or ""),
            }
        )

    # Summary
    summary_text = ""
    if profile.summary:
        summary_text = esc(profile.summary.source_text)

    return {
        "name": esc(profile.owner.full_name),
        "contact": contact,
        "summary": summary_text,
        "skills": skill_groups,
        "experience": experience_list,
        "projects": project_list,
        "education": education_list,
        "certifications": cert_list,
        "publications": [],
        "awards": [],
    }


def render_latex(
    profile: CanonicalProfile,
    plan: ResumePlan,
    generated_bullets: list[GeneratedBullet] | None = None,
    bold_keywords: list[str] | None = None,
    template_dir: Path | None = None,
    template_id: str = "ats-modern",
) -> str:
    """Render a complete .tex file from profile and plan.

    Returns the LaTeX source as a string.
    """
    tpl_dir = template_dir or _DEFAULT_TEMPLATE_DIR
    tpl_path = tpl_dir / template_id

    env = Environment(
        loader=FileSystemLoader(str(tpl_path)),
        block_start_string="{%",
        block_end_string="%}",
        variable_start_string="{{",
        variable_end_string="}}",
        comment_start_string="{#",
        comment_end_string="#}",
        autoescape=False,
    )

    template = env.get_template("main.tex.j2")
    context = build_template_context(profile, plan, generated_bullets, bold_keywords)
    return template.render(**context)
