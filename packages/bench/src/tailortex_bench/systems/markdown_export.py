"""Plain-text rendering shim for pre-harness product commits.

The pinned Stage 0 main commit has no export_markdown function.
"""

from __future__ import annotations

from pathlib import Path

from tailortex.schemas.profile import CanonicalProfile
from tailortex.schemas.resume import GeneratedBullet, ResumePlan


def export_markdown(
    profile: CanonicalProfile,
    plan: ResumePlan,
    output_path: Path,
    generated_bullets: list[GeneratedBullet] | None = None,
) -> Path:
    """Export approved, selected profile content as plain Markdown."""
    replacements = {
        source_id: bullet.text
        for bullet in generated_bullets or []
        for source_id in bullet.source_bullet_ids
    }
    lines = [profile.owner.full_name]
    headings: set[str] = set()
    if profile.summary and profile.summary.approved:
        lines.extend(["", "Summary", profile.summary.source_text])
    for section in plan.sections:
        if section.type == "experience":
            experiences = [
                e for e in profile.experiences if e.id in section.source_ids and e.approved
            ]
            if experiences and section.type not in headings:
                lines.extend(["", "Experience"])
                headings.add(section.type)
            for experience in experiences:
                lines.append(f"{experience.title} | {experience.organization}")
                lines.append(f"{experience.start_date} - {experience.end_date or 'Present'}")
                lines.extend(
                    f"- {replacements.get(b.id, b.text)}"
                    for b in experience.bullets
                    if b.approved and b.id in section.selected_bullet_ids
                )
        elif section.type == "project":
            projects = [p for p in profile.projects if p.id in section.source_ids and p.approved]
            if projects and section.type not in headings:
                lines.extend(["", "Projects"])
                headings.add(section.type)
            for project in projects:
                lines.append(project.name)
                lines.extend(
                    f"- {replacements.get(b.id, b.text)}"
                    for b in project.bullets
                    if b.approved and b.id in section.selected_bullet_ids
                )
        elif section.type == "education":
            education = [e for e in profile.education if e.id in section.source_ids and e.approved]
            if education and section.type not in headings:
                lines.extend(["", "Education"])
                headings.add(section.type)
            for school in education:
                lines.append(school.institution)
                lines.append(" ".join(part for part in [school.degree, school.field] if part))
                dates = " - ".join(part for part in [school.start_date, school.end_date] if part)
                if dates:
                    lines.append(dates)
    skills = [skill.name for skill in profile.skills if skill.approved]
    if skills:
        lines.extend(["", "Skills", ", ".join(skills)])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output_path
