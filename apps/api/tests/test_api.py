"""HTTP contracts against a temporary local workspace."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import tailortex_api.main as api
from tailortex.storage.workspace import Workspace


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
    assert client.get(f"/applications/{job_id}").json()["job_id"] == job_id
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
def test_tailor_and_render_report_missing_profile_or_jd(
    client: TestClient, route: str
) -> None:
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
