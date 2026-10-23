"""In-process product adapter."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any

import tailortex
from tailortex.llm.rewriter import rewrite_bullets_deterministic
from tailortex.matching.selector import select_for_resume
from tailortex.parsers.jd_parser import parse_jd_text
from tailortex.parsers.resume_parser import parse_resume_text

from tailortex_bench.corpus import Case

try:
    from tailortex.rendering.exporter import export_markdown
except ImportError:
    from tailortex_bench.systems.markdown_export import export_markdown


def product_commit() -> str | None:
    source = Path(tailortex.__file__).resolve()
    result = subprocess.run(
        ["git", "-C", str(source.parent), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


class TailorTex:
    id = "tailortex"
    kind = "tailortex"

    def run(self, case: Case) -> dict[str, Any]:
        profile = parse_resume_text(case.resume).profile
        if profile.summary:
            profile.summary.approved = True
        for entry in profile.experiences:
            entry.approved = True
            for bullet in entry.bullets:
                bullet.approved = True
        for project in profile.projects:
            project.approved = True
            for bullet in project.bullets:
                bullet.approved = True
        for education in profile.education:
            education.approved = True
        for skill in profile.skills:
            skill.approved = True
        job = parse_jd_text(case.job).jd
        plan = select_for_resume(profile, job)
        bullets = [bullet for entry in profile.experiences for bullet in entry.bullets]
        bullets.extend(bullet for entry in profile.projects for bullet in entry.bullets)
        generated = rewrite_bullets_deterministic(bullets, job.required_skills)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "resume.md"
            export_markdown(profile, plan, path, generated)
            text = path.read_text(encoding="utf-8")
        version = getattr(tailortex, "__version__", "0.1.0")
        commit = product_commit()
        return {
            "text": text,
            "model": None,
            "version": f"{version}+{commit}" if commit else version,
        }
