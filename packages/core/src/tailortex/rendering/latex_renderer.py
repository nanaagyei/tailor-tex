"""LaTeX renderer — converts profile + resume plan into .tex output.

Uses Jinja2 templates with LaTeX escaping.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from tailortex.schemas.profile import CanonicalProfile
from tailortex.schemas.resume import GeneratedBullet, ResumePlan

# LaTeX special characters handled in escape_latex().

# Default template directory (sibling packages/templates).
_DEFAULT_TEMPLATE_DIR = Path(__file__).resolve().parents[4] / "templates"

_month_abbr: dict[str, str] = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
    "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
}


def _format_month_year(iso_date: str) -> str:
    """Convert ISO partial date like '2022-01' to 'Jan 2022'."""
    if not iso_date or "-" not in iso_date:
        return iso_date
    parts = iso_date.split("-", 1)
    if len(parts) != 2:
        return iso_date
    year, month = parts
    return f"{_month_abbr.get(month, month)} {year}"


def _discover_templates(template_dir: Path) -> dict[str, Path]:
    """Recursively scan for template directories containing metadata.json.

    Returns dict mapping template id -> directory path.
    """
    discovered: dict[str, Path] = {}
    for metadata_path in template_dir.rglob("metadata.json"):
        try:
            meta = json.loads(metadata_path.read_text(encoding="utf-8"))
            template_id = meta.get("id")
            if template_id:
                discovered[template_id] = metadata_path.parent
        except (json.JSONDecodeError, KeyError):
            continue
    return discovered


def list_templates(template_dir: Path | None = None) -> dict[str, dict]:
    """Return available templates with their metadata.

    Returns dict mapping template_id -> metadata dict.
    """
    tpl_dir = template_dir or _DEFAULT_TEMPLATE_DIR
    result: dict[str, dict] = {}
    for template_id, dir_path in _discover_templates(tpl_dir).items():
        metadata_path = dir_path / "metadata.json"
        try:
            result[template_id] = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            continue
    return result


def get_template_path(
    template_id: str,
    template_dir: Path | None = None,
) -> Path:
    """Return the path to a template's main.tex.j2 file.

    Raises FileNotFoundError if the template is not found.
    """
    tpl_dir = template_dir or _DEFAULT_TEMPLATE_DIR
    discovered = _discover_templates(tpl_dir)
    if template_id not in discovered:
        available = ", ".join(sorted(discovered)) or "(none)"
        raise FileNotFoundError(
            f"Template '{template_id}' not found. Available: {available}"
        )
    return discovered[template_id] / "main.tex.j2"


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
    escape: bool = True,
) -> dict[str, Any]:
    """Build the template context dict from profile + plan."""
    if escape:
        esc = escape_latex
    else:
        def esc(text: str) -> str:
            return text
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

        start_fmt = _format_month_year(exp.start_date or "")
        end_fmt = ""
        if exp.end_date:
            end_fmt = _format_month_year(exp.end_date)
        elif exp.is_current:
            end_fmt = "Present"

        if end_fmt:
            dates = f"{start_fmt} -- {end_fmt}"
        else:
            dates = start_fmt

        experience_list.append(
            {
                "title": esc(exp.title),
                "organization": esc(exp.organization),
                "location": esc(exp.location or ""),
                "dates": esc(dates),
                "start_date": exp.start_date or "",
                "end_date": exp.end_date or "",
                "is_current": exp.is_current,
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
        start_fmt = _format_month_year(edu.start_date or "")
        end_fmt = _format_month_year(edu.end_date) if edu.end_date else ""

        if end_fmt:
            dates = f"{start_fmt} -- {end_fmt}"
        else:
            dates = start_fmt

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

    # Publications
    publication_list: list[dict[str, Any]] = []
    for pub in profile.publications:
        publication_list.append(
            {
                "title": esc(pub.title),
                "venue": esc(pub.venue or ""),
                "date": esc(pub.date or ""),
                "url": esc(pub.url or ""),
            }
        )

    # Awards
    award_list: list[dict[str, Any]] = []
    for award in profile.awards:
        award_list.append(
            {
                "title": esc(award.title),
                "issuer": esc(award.issuer or ""),
                "date": esc(award.date or ""),
            }
        )

    # Summary
    summary_text = ""
    if profile.summary:
        summary_text = esc(profile.summary.source_text)

    # Publications
    publication_list: list[dict[str, Any]] = []
    for pub in profile.publications:
        pub_date = _format_month_year(pub.date) if pub.date else ""
        publication_list.append(
            {
                "title": esc(pub.title),
                "venue": esc(pub.venue or ""),
                "date": esc(pub_date),
                "url": esc(pub.url or ""),
            }
        )

    # Awards
    award_list: list[dict[str, Any]] = []
    for award in profile.awards:
        award_date = _format_month_year(award.date) if award.date else ""
        award_list.append(
            {
                "title": esc(award.title),
                "issuer": esc(award.issuer or ""),
                "date": esc(award_date),
            }
        )

    return {
        "name": esc(profile.owner.full_name),
        "contact": contact,
        "summary": summary_text,
        "skills": skill_groups,
        "experience": experience_list,
        "projects": project_list,
        "education": education_list,
        "certifications": cert_list,
        "publications": publication_list,
        "awards": award_list,
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
    tpl_path = get_template_path(template_id, tpl_dir)

    env = Environment(
        loader=FileSystemLoader(str(tpl_path.parent)),
        block_start_string="{%",
        block_end_string="%}",
        variable_start_string="{{",
        variable_end_string="}}",
        comment_start_string="{#",
        comment_end_string="#}",
        autoescape=False,
    )
    env.filters["format_date"] = _format_month_year

    template = env.get_template("main.tex.j2")
    context = build_template_context(profile, plan, generated_bullets, bold_keywords)
    return template.render(**context)
