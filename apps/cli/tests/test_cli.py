"""CLI command contracts against an isolated local workspace."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tailortex_cli.main import app


runner = CliRunner()


def invoke(workspace: Path, *args: str):
    return runner.invoke(app, [*args, "--workspace", str(workspace)])


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


@pytest.mark.xfail(strict=True, reason="Issue #7: import uses model_dump on a ProfileDraft")
def test_import_creates_reviewable_draft(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    resume = tmp_path / "resume.txt"
    resume.write_text("Jordan Example\nSkills\nPython\n", encoding="utf-8")

    result = invoke(workspace, "import", str(resume))

    assert result.exit_code == 0
    assert "Profile draft saved" in result.output


@pytest.mark.xfail(strict=True, reason="Issue #7: JD parse uses fields missing on JDParseResult")
def test_jd_parse_saves_job(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    description = tmp_path / "job.txt"
    description.write_text("Senior QA Engineer. Required: Python.", encoding="utf-8")

    result = invoke(workspace, "jd", "parse", str(description))

    assert result.exit_code == 0
    assert "Parsed Job Description" in result.output
