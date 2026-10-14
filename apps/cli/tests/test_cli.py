"""CLI command contracts against an isolated local workspace."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tailortex.parsers.jd_parser import parse_jd_text
from tailortex.schemas.profile import CanonicalProfile
from tailortex.storage.workspace import Workspace
from tailortex_cli.main import app


runner = CliRunner()


def invoke(workspace: Path, *args: str):
    return runner.invoke(app, [*args, "--workspace", str(workspace)])


def write_synthetic_inputs(tmp_path: Path) -> tuple[Path, Path]:
    resume = tmp_path / "resume.txt"
    resume.write_text(
        "Jordan Example\nExperience\nQA Engineer | Example Systems\n"
        "January 2022 - Present\n- Automated Python tests for release checks.\n"
        "Skills\nPython\n",
        encoding="utf-8",
    )
    jd = tmp_path / "job.txt"
    jd.write_text("QA Engineer. Required: Python experience.", encoding="utf-8")
    return resume, jd


def test_version() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "tailortex 0.1.0" in result.output


def test_init_workspace_commands_and_empty_profiles(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    first = invoke(workspace, "init")
    second = invoke(workspace, "init")
    listing = invoke(workspace, "workspace", "list")
    info = invoke(workspace, "workspace", "info")
    profiles = invoke(workspace, "profile", "list")

    assert first.exit_code == second.exit_code == listing.exit_code == info.exit_code == 0
    assert profiles.exit_code == 0
    assert (workspace / "config.json").exists()
    assert "already exists" in second.output
    assert "Profiles (0)" in listing.output
    assert "Applications (0)" in listing.output
    assert "Profiles: 0" in info.output
    assert "No profiles found" in profiles.output


def test_profile_approve_review_and_list(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    profile_file = tmp_path / "profile.json"
    profile_file.write_text(
        json.dumps({"profile_id": "candidate", "owner": {"full_name": "Jordan Example"}}),
        encoding="utf-8",
    )

    approved = invoke(workspace, "profile", "approve", str(profile_file))
    reviewed = invoke(workspace, "profile", "review", "--profile", "candidate")
    listed = invoke(workspace, "profile", "list")

    assert approved.exit_code == reviewed.exit_code == listed.exit_code == 0
    assert (workspace / "profiles" / "candidate.json").exists()
    assert "Profile approved: candidate" in approved.output
    assert "Jordan Example" in reviewed.output
    assert "candidate" in listed.output


def test_profile_approval_rejects_invalid_json(tmp_path: Path) -> None:
    profile_file = tmp_path / "invalid.json"
    profile_file.write_text("{invalid", encoding="utf-8")

    result = invoke(tmp_path / "workspace", "profile", "approve", str(profile_file))

    assert result.exit_code == 2
    assert "Invalid profile" in result.output


@pytest.mark.parametrize(
    ("args", "exit_code", "message"),
    [
        (("import", "missing.txt"), 3, "File not found"),
        (("jd", "parse", "missing.txt"), 3, "Provide a file or use --stdin"),
        (("profile", "approve", "missing.json"), 1, "File not found"),
        (("profile", "review"), 1, "No workspace found"),
        (("profile", "list"), 1, "No workspace found"),
        (("tailor", "--jd", "missing"), 1, "No workspace found"),
        (("export", "--application", "missing"), 1, "No workspace found"),
        (("validate", "--application", "missing"), 1, "No workspace found"),
        (("workspace", "list"), 1, "No workspace found"),
        (("workspace", "info"), 1, "No workspace found"),
        (("config", "get"), 1, "No workspace found"),
    ],
)
def test_missing_inputs_have_actionable_errors(
    tmp_path: Path, args: tuple[str, ...], exit_code: int, message: str
) -> None:
    result = invoke(tmp_path / "workspace", *args)

    assert result.exit_code == exit_code
    assert message in result.output


def test_config_set_and_get(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    saved = invoke(workspace, "config", "set", "provider.name", "local")
    loaded = invoke(workspace, "config", "get")

    assert saved.exit_code == loaded.exit_code == 0
    assert json.loads((workspace / "config.json").read_text(encoding="utf-8"))["provider"] == {
        "name": "local"
    }
    assert '"name": "local"' in loaded.output


def test_import_creates_reviewable_draft(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    resume, _ = write_synthetic_inputs(tmp_path)

    result = invoke(workspace, "import", str(resume))
    reviewed = invoke(workspace, "profile", "review")

    assert result.exit_code == 0
    assert "Profile draft saved" in result.output
    assert (workspace / "drafts" / "default.json").exists()
    assert (workspace / "drafts" / "default.source.txt").read_text() == resume.read_text().strip()
    assert list((workspace / "applications").iterdir()) == []
    assert reviewed.exit_code == 0
    assert "Showing DRAFT (not approved)" in reviewed.output


def test_jd_parse_saves_job(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _, description = write_synthetic_inputs(tmp_path)

    result = invoke(
        workspace,
        "jd",
        "parse",
        str(description),
        "--company",
        "Example Systems",
        "--role",
        "QA Engineer",
    )

    assert result.exit_code == 0
    assert "Parsed Job Description" in result.output
    assert len(list((workspace / "jobs").glob("*.json"))) == 1
    assert list((workspace / "applications").iterdir()) == []
    listing = invoke(workspace, "jd", "list")
    assert listing.exit_code == 0
    assert "Example Systems" in listing.output
    assert "QA Engineer" in listing.output


def test_approve_all_and_option_conflicts(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    resume, _ = write_synthetic_inputs(tmp_path)
    imported = invoke(workspace, "import", str(resume), "--profile", "candidate")
    assert imported.exit_code == 0
    no_args = invoke(workspace, "profile", "approve")
    conflict = invoke(workspace, "profile", "approve", str(resume), "--all")
    assert no_args.exit_code == conflict.exit_code == 1
    assert "profile approve FILE" in no_args.output
    assert "profile approve --all" in no_args.output

    approved = invoke(workspace, "profile", "approve", "--all", "--profile", "candidate")
    assert approved.exit_code == 0
    assert not (workspace / "drafts" / "candidate.json").exists()
    assert not (workspace / "drafts" / "candidate.source.txt").exists()
    profile = Workspace(workspace).load_profile("candidate")
    assert all(exp.approved and all(b.approved for b in exp.bullets) for exp in profile.experiences)
    assert all(skill.approved for skill in profile.skills)
    assert (
        "Showing APPROVED PROFILE"
        in invoke(workspace, "profile", "review", "--profile", "candidate").output
    )


def test_approve_all_marks_every_profile_item(tmp_path: Path) -> None:
    workspace = Workspace(tmp_path / "workspace")
    workspace.init()
    profile = CanonicalProfile.model_validate(
        {
            "owner": {"full_name": "Jordan Example"},
            "summary": {"source_text": "QA engineer"},
            "experiences": [
                {
                    "id": "exp-1",
                    "organization": "Example Systems",
                    "title": "QA Engineer",
                    "start_date": "2022",
                    "bullets": [{"id": "bullet-1", "text": "Automated Python tests"}],
                }
            ],
            "projects": [
                {
                    "id": "project-1",
                    "name": "Test suite",
                    "bullets": [{"id": "bullet-2", "text": "Built tests"}],
                }
            ],
            "education": [
                {
                    "id": "education-1",
                    "institution": "Example University",
                    "degree": "BS",
                    "field": "Computer Science",
                }
            ],
            "skills": [{"name": "Python"}],
            "certifications": [{"id": "cert-1", "name": "QA", "issuer": "Example"}],
            "publications": [{"id": "pub-1", "title": "Testing"}],
            "awards": [{"id": "award-1", "title": "Excellence"}],
        }
    )
    workspace.save_draft(profile, "Synthetic resume text")
    result = invoke(workspace.root, "profile", "approve", "--all")
    assert result.exit_code == 0, result.output
    approved = workspace.load_profile()
    assert approved.summary and approved.summary.approved
    assert all(
        item.approved
        for group in (
            approved.experiences,
            approved.projects,
            approved.education,
            approved.skills,
            approved.certifications,
            approved.publications,
            approved.awards,
        )
        for item in group
    )
    assert all(bullet.approved for exp in approved.experiences for bullet in exp.bullets)
    assert all(bullet.approved for project in approved.projects for bullet in project.bullets)


def test_import_to_tex_by_id_and_unapproved_exit(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    resume, description = write_synthetic_inputs(tmp_path)
    assert invoke(workspace, "init").exit_code == 0
    assert invoke(workspace, "import", str(resume)).exit_code == 0
    assert invoke(workspace, "profile", "review").exit_code == 0
    assert invoke(workspace, "tailor", "--jd", str(description)).exit_code == 2
    assert invoke(workspace, "profile", "approve", "--all").exit_code == 0
    parsed = invoke(workspace, "jd", "parse", str(description))
    assert parsed.exit_code == 0
    job_id = next((workspace / "jobs").glob("*.json")).stem
    assert job_id in parsed.output
    assert job_id in invoke(workspace, "jd", "list").output
    output = tmp_path / "out.tex"
    tailored = invoke(workspace, "tailor", "--jd", job_id, "--output", str(output))
    assert tailored.exit_code == 0, tailored.output
    assert "\\documentclass" in output.read_text(encoding="utf-8")
    assert "Jordan Example" in output.read_text(encoding="utf-8")
    assert "Drafts (0)" in invoke(workspace, "workspace", "list").output
    assert "Jobs (1)" in invoke(workspace, "workspace", "list").output


def test_tailor_file_saves_job_and_unknown_id_is_actionable(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    resume, description = write_synthetic_inputs(tmp_path)
    assert invoke(workspace, "import", str(resume)).exit_code == 0
    assert invoke(workspace, "profile", "approve", "--all").exit_code == 0
    output = tmp_path / "file.tex"
    assert (
        invoke(workspace, "tailor", "--jd", str(description), "--output", str(output)).exit_code
        == 0
    )
    assert len(list((workspace / "jobs").glob("*.json"))) == 1
    missing = invoke(workspace, "tailor", "--jd", "missing")
    assert missing.exit_code == 1
    assert "JD not found: missing. Run 'tailortex jd list'." in missing.output


@pytest.mark.parametrize("shape", ["nested", "flat"])
def test_tailor_legacy_job_id(tmp_path: Path, shape: str) -> None:
    workspace = tmp_path / "workspace"
    resume, _ = write_synthetic_inputs(tmp_path)
    assert invoke(workspace, "import", str(resume)).exit_code == 0
    assert invoke(workspace, "profile", "approve", "--all").exit_code == 0
    parsed = parse_jd_text("QA Engineer requires Python")
    payload = parsed.jd.model_dump(mode="json")
    if shape == "nested":
        payload = {"jd": payload, "raw_text": parsed.raw_text, "warnings": parsed.warnings}
    Workspace(workspace).save_application(parsed.jd.job_id, payload)
    output = tmp_path / f"legacy-{shape}.tex"
    result = invoke(workspace, "tailor", "--jd", parsed.jd.job_id, "--output", str(output))
    assert result.exit_code == 0, result.output
    assert output.exists()
