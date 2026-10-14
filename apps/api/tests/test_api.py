"""HTTP contracts against a temporary local workspace."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

import tailortex_api.main as api
from tailortex.parsers.jd_parser import parse_jd_text
from tailortex.storage.workspace import Workspace
from tailortex_cli.main import app as cli_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    workspace = Workspace(tmp_path / "workspace")
    workspace.init()
    monkeypatch.setattr(api, "_ws", lambda: workspace)
    with TestClient(api.app) as test_client:
        yield test_client


def sample_profile() -> dict:
    return {"profile_id": "candidate", "owner": {"full_name": "Jordan Example"}}


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_profile_lifecycle_and_missing_profile(client: TestClient) -> None:
    assert client.get("/profiles").json() == []

    saved = client.post("/profiles", json=sample_profile())
    fetched = client.get("/profiles/candidate")
    listed = client.get("/profiles")
    deleted = client.delete("/profiles/candidate")

    assert saved.status_code == 200
    assert saved.json() == {"status": "saved", "profile_id": "candidate"}
    assert fetched.status_code == 200
    assert fetched.json()["owner"]["full_name"] == "Jordan Example"
    assert listed.json() == ["candidate"]
    assert deleted.json() == {"status": "deleted", "profile_id": "candidate"}
    assert client.get("/profiles/candidate").status_code == 404
    assert client.delete("/profiles/candidate").status_code == 404


def test_profile_rejects_missing_owner(client: TestClient) -> None:
    response = client.post("/profiles", json={"profile_id": "candidate"})

    assert response.status_code == 422
    assert client.get("/profiles").json() == []


def test_import_plain_text_and_reject_empty_or_unsupported_file(client: TestClient) -> None:
    imported = client.post(
        "/import", files={"file": ("resume.txt", b"Jordan Example\nSkills\nPython\n")}
    )
    empty = client.post("/import", files={"file": ("empty.txt", b"")})
    unsupported = client.post("/import", files={"file": ("resume.bin", b"data")})

    assert imported.status_code == 200
    assert imported.json()["status"] == "imported"
    assert imported.json()["draft"]["owner"]["full_name"] == "Jordan Example"
    assert empty.status_code == 422
    assert unsupported.status_code == 422


def test_jd_and_application_lifecycle(client: TestClient) -> None:
    parsed = client.post(
        "/jd/parse",
        json={
            "text": "Senior QA Engineer. Required: Python.",
            "company": "Example Systems",
            "role_title": "QA Engineer",
        },
    )

    assert parsed.status_code == 200
    job = parsed.json()
    job_id = job["job_id"]
    assert job["company"] == "Example Systems"
    assert "python" in [skill.lower() for skill in job["required_skills"]]
    assert client.get("/applications").json() == [job_id]
    assert client.get(f"/applications/{job_id}").json() == job
    assert client.delete(f"/applications/{job_id}").json() == {
        "status": "deleted",
        "app_id": job_id,
    }
    assert client.get(f"/applications/{job_id}").status_code == 404
    assert client.delete(f"/applications/{job_id}").status_code == 404


def test_tailor_and_render_use_saved_profile_and_jd(client: TestClient) -> None:
    client.post("/profiles", json=sample_profile())
    parsed = client.post(
        "/jd/parse",
        json={"text": "Senior QA Engineer. Required: Python.", "company": "Example Systems"},
    )
    job_id = parsed.json()["job_id"]

    tailored = client.post("/tailor", json={"profile_id": "candidate", "jd_id": job_id})
    rendered = client.post("/render", json={"profile_id": "candidate", "jd_id": job_id})

    assert tailored.status_code == 200
    assert set(tailored.json()) == {"plan", "generated_bullets", "validation"}
    assert rendered.status_code == 200
    assert "\\documentclass" in rendered.json()["tex"]


@pytest.mark.parametrize("route", ["/tailor", "/render"])
def test_tailor_and_render_report_missing_profile_or_jd(client: TestClient, route: str) -> None:
    missing_profile = client.post(route, json={"profile_id": "missing", "jd_id": "missing"})
    client.post("/profiles", json=sample_profile())
    missing_jd = client.post(route, json={"profile_id": "candidate", "jd_id": "missing"})

    assert missing_profile.status_code == 404
    assert "Profile not found" in missing_profile.json()["detail"]
    assert missing_jd.status_code == 404
    assert "JD not found" in missing_jd.json()["detail"]


def test_config_round_trip(client: TestClient) -> None:
    assert client.get("/config").json() == {"version": "1.0.0"}

    saved = client.put("/config", json={"provider": {"name": "local"}})

    assert saved.json() == {"status": "saved"}
    assert client.get("/config").json() == {"provider": {"name": "local"}}


def test_api_import_can_be_reviewed_and_approved_by_cli(client: TestClient, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    text = (
        "Jordan Example\nExperience\nQA Engineer | Example Systems\n"
        "January 2022 - Present\n- Automated Python tests.\nSkills\nPython\n"
    )
    imported = client.post("/import", files={"file": ("resume.txt", text.encode())})
    assert imported.status_code == 200
    assert set(imported.json()) == {"status", "draft", "warnings"}
    assert (workspace / "drafts" / "default.source.txt").read_text() == text.strip()
    runner = CliRunner()
    reviewed = runner.invoke(cli_app, ["profile", "review", "--workspace", str(workspace)])
    approved = runner.invoke(
        cli_app, ["profile", "approve", "--all", "--workspace", str(workspace)]
    )
    assert reviewed.exit_code == approved.exit_code == 0
    assert "Showing DRAFT (not approved)" in reviewed.output
    assert client.get("/profiles/default").json()["owner"]["full_name"] == "Jordan Example"
    assert not (workspace / "drafts" / "default.source.txt").exists()


def test_api_job_can_be_tailored_by_cli_and_cli_job_by_api(
    client: TestClient, tmp_path: Path
) -> None:
    workspace = tmp_path / "workspace"
    runner = CliRunner()
    client.post("/profiles", json=sample_profile())
    api_job = client.post(
        "/jd/parse", json={"text": "QA Engineer requires Python", "company": "Example Systems"}
    )
    api_id = api_job.json()["job_id"]
    assert Workspace(workspace).load_job(api_id).raw_text == "QA Engineer requires Python"
    output = tmp_path / "api-job.tex"
    cli_tailor = runner.invoke(
        cli_app,
        [
            "tailor",
            "--profile",
            "candidate",
            "--jd",
            api_id,
            "--output",
            str(output),
            "--workspace",
            str(workspace),
        ],
    )
    assert cli_tailor.exit_code == 0, cli_tailor.output
    assert output.exists()

    description = tmp_path / "cli-job.txt"
    description.write_text("QA Engineer requires SQL", encoding="utf-8")
    cli_parse = runner.invoke(
        cli_app, ["jd", "parse", str(description), "--workspace", str(workspace)]
    )
    assert cli_parse.exit_code == 0, cli_parse.output
    cli_id = next(path.stem for path in (workspace / "jobs").glob("*.json") if path.stem != api_id)
    assert (
        client.post("/tailor", json={"profile_id": "candidate", "jd_id": cli_id}).status_code == 200
    )
    assert (
        client.post("/render", json={"profile_id": "candidate", "jd_id": cli_id}).status_code == 200
    )
    assert sorted(client.get("/applications").json()) == sorted([api_id, cli_id])


@pytest.mark.parametrize("shape", ["nested", "flat"])
def test_legacy_job_shapes_work_through_api_aliases(
    client: TestClient, tmp_path: Path, shape: str
) -> None:
    workspace = Workspace(tmp_path / "workspace")
    client.post("/profiles", json=sample_profile())
    parsed = parse_jd_text("QA Engineer requires Python")
    payload = parsed.jd.model_dump(mode="json")
    if shape == "nested":
        payload = {"jd": payload, "raw_text": parsed.raw_text, "warnings": parsed.warnings}
    workspace.save_application(parsed.jd.job_id, payload)
    workspace.save_application("unrelated", {"status": "draft"})
    assert client.get("/applications").json() == [parsed.jd.job_id]
    assert client.get(f"/applications/{parsed.jd.job_id}").json() == parsed.jd.model_dump(
        mode="json"
    )
    assert (
        client.post(
            "/tailor", json={"profile_id": "candidate", "jd_id": parsed.jd.job_id}
        ).status_code
        == 200
    )
    assert client.delete(f"/applications/{parsed.jd.job_id}").status_code == 200
    assert workspace.load_application("unrelated") == {"status": "draft"}
