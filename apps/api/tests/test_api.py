"""Comprehensive API tests for TailorTex API.

Uses TestClient and isolated temporary workspaces via monkeypatching
_ws() so tests never touch ~/.tailortex/.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tailortex.storage.workspace import Workspace

# ── Sample data ─────────────────────────────────────────────────

SAMPLE_RESUME = """\
Morgan Castillo
morgan.castillo@proton.me | (512) 847-1928
Austin, TX

Summary
Software engineer with 4 years of experience building backend services.

Experience

Software Engineer | Meridian Systems
Austin, TX
Mar 2023 - Present
- Designed and maintained CI/CD pipelines using GitHub Actions, reducing deploy time by 40%
- Built REST API endpoints in Python (FastAPI) serving 2M+ requests/day
"""

SAMPLE_JD = (
    "Senior Backend Engineer\n"
    "Required skills: Python, Docker, REST APIs, PostgreSQL.\n"
    "Experience with CI/CD pipelines and microservices preferred."
)


# ── Profile helpers ────────────────────────────────────────────


def _make_approved_profile(profile_id: str = "default") -> dict[str, Any]:
    """Return a dict for a CanonicalProfile with approved experiences."""
    return {
        "profile_id": profile_id,
        "version": "1.0.0",
        "owner": {
            "full_name": "Morgan Castillo",
            "email": "morgan.castillo@proton.me",
            "phone": "(512) 847-1928",
            "location": "Austin, TX",
            "links": [],
        },
        "summary": {
            "source_text": "Software engineer with 4 years of experience building backend services.",
            "approved": True,
        },
        "experiences": [
            {
                "id": "exp_001",
                "organization": "Meridian Systems",
                "title": "Software Engineer",
                "location": "Austin, TX",
                "start_date": "2023-03",
                "end_date": None,
                "is_current": True,
                "approved": True,
                "bullets": [
                    {
                        "id": "bullet_001",
                        "text": "Designed and maintained CI/CD pipelines using GitHub Actions, reducing deploy time by 40%",
                        "skills": ["CI/CD", "GitHub Actions"],
                        "metrics": ["40%"],
                        "evidence_ids": [],
                        "approved": True,
                    },
                    {
                        "id": "bullet_002",
                        "text": "Built REST API endpoints in Python (FastAPI) serving 2M+ requests/day",
                        "skills": ["Python", "FastAPI", "REST APIs"],
                        "metrics": ["2M+"],
                        "evidence_ids": [],
                        "approved": True,
                    },
                ],
            }
        ],
        "projects": [
            {
                "id": "proj_001",
                "name": "Microservice Migration",
                "description": "Migrated monolith to microservices",
                "url": None,
                "skills": ["Docker", "PostgreSQL", "Python"],
                "approved": True,
                "bullets": [
                    {
                        "id": "bullet_003",
                        "text": "Led migration of 5 services from monolith to Docker-based microservices",
                        "skills": ["Docker", "Microservices"],
                        "metrics": ["5"],
                        "evidence_ids": [],
                        "approved": True,
                    }
                ],
            }
        ],
        "education": [
            {
                "id": "edu_001",
                "institution": "University of Texas",
                "degree": "B.S.",
                "field": "Computer Science",
                "start_date": "2019",
                "end_date": "2023",
                "gpa": None,
                "approved": True,
            }
        ],
        "skills": [
            {"name": "Python", "category": "Languages", "proficiency": "advanced", "approved": True},
            {"name": "Docker", "category": "DevOps", "proficiency": "intermediate", "approved": True},
            {"name": "PostgreSQL", "category": "Databases", "proficiency": "intermediate", "approved": True},
            {"name": "FastAPI", "category": "Frameworks", "proficiency": "advanced", "approved": True},
            {"name": "REST APIs", "category": "Concepts", "proficiency": "advanced", "approved": True},
            {"name": "CI/CD", "category": "DevOps", "proficiency": "intermediate", "approved": True},
        ],
        "certifications": [],
        "publications": [],
        "awards": [],
        "evidence_ledger": [],
    }


def _make_unapproved_profile(profile_id: str = "default") -> dict[str, Any]:
    """Return a dict for a CanonicalProfile with approved=False on all items."""
    profile = _make_approved_profile(profile_id)
    profile["summary"]["approved"] = False
    for exp in profile["experiences"]:
        exp["approved"] = False
        for b in exp["bullets"]:
            b["approved"] = False
    for proj in profile["projects"]:
        proj["approved"] = False
        for b in proj["bullets"]:
            b["approved"] = False
    for edu in profile["education"]:
        edu["approved"] = False
    for skill in profile.get("skills", []):
        skill["approved"] = False
    return profile


# ── Fixtures ───────────────────────────────────────────────────


@pytest.fixture
def workspace_root(tmp_path: Path) -> Path:
    """Temp workspace root directory."""
    return tmp_path / "workspace"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, workspace_root: Path) -> TestClient:
    """TestClient with isolated workspace in a temp directory.

    Monkeypatches the _ws() factory function in tailortex_api.main
    so every endpoint call constructs a Workspace rooted at the
    temp directory instead of ~/.tailortex/.
    """
    import tailortex_api.main

    def _ws() -> Workspace:
        ws = Workspace(root=workspace_root)
        if not ws.exists():
            ws.init()
        return ws

    monkeypatch.setattr(tailortex_api.main, "_ws", _ws)

    from tailortex_api.main import app

    return TestClient(app)


# ── Tests: Health ──────────────────────────────────────────────


class TestHealth:
    def test_health_returns_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


# ── Tests: Profiles ────────────────────────────────────────────


class TestProfiles:
    def test_list_profiles_empty(self, client: TestClient) -> None:
        response = client.get("/profiles")
        assert response.status_code == 200
        assert response.json() == []

    def test_save_and_get_profile(self, client: TestClient) -> None:
        profile = _make_approved_profile("test-profile")
        save_resp = client.post("/profiles", json=profile)
        assert save_resp.status_code == 200
        assert save_resp.json() == {"status": "saved", "profile_id": "test-profile"}

        get_resp = client.get("/profiles/test-profile")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["profile_id"] == "test-profile"
        assert data["owner"]["full_name"] == "Morgan Castillo"
        assert len(data["experiences"]) == 1
        assert data["experiences"][0]["approved"] is True

    def test_list_profiles_after_save(self, client: TestClient) -> None:
        client.post("/profiles", json=_make_approved_profile("p1"))
        client.post("/profiles", json=_make_approved_profile("p2"))
        response = client.get("/profiles")
        assert response.status_code == 200
        assert sorted(response.json()) == ["p1", "p2"]

    def test_delete_profile(self, client: TestClient) -> None:
        client.post("/profiles", json=_make_approved_profile("to-delete"))
        del_resp = client.delete("/profiles/to-delete")
        assert del_resp.status_code == 200
        assert del_resp.json() == {"status": "deleted", "profile_id": "to-delete"}

        get_resp = client.get("/profiles/to-delete")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_profile(self, client: TestClient) -> None:
        response = client.delete("/profiles/noexist")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_nonexistent_profile(self, client: TestClient) -> None:
        response = client.get("/profiles/noexist")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ── Tests: Import ──────────────────────────────────────────────


class TestImport:
    def test_import_resume_file_returns_draft(self, client: TestClient) -> None:
        files = {
            "file": ("resume.txt", io.BytesIO(SAMPLE_RESUME.encode("utf-8")), "text/plain"),
        }
        response = client.post("/import", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "imported"
        assert "draft" in data
        draft = data["draft"]
        assert draft["owner"]["full_name"] == "Morgan Castillo"
        assert len(draft["experiences"]) >= 1

    def test_import_missing_file_returns_422(self, client: TestClient) -> None:
        response = client.post("/import")
        assert response.status_code == 422


# ── Tests: JD Parsing ──────────────────────────────────────────


class TestJDParse:
    def test_parse_jd_returns_structured_data(self, client: TestClient) -> None:
        payload = {
            "text": SAMPLE_JD,
            "company": "Meridian Systems",
            "role_title": "Senior Backend Engineer",
        }
        response = client.post("/jd/parse", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"].startswith("jd-")
        assert data["company"] == "Meridian Systems"
        assert data["role_title"] == "Senior Backend Engineer"
        req_lower = [s.lower() for s in data["required_skills"]]
        assert "python" in req_lower
        assert "docker" in req_lower
        assert "rest apis" in req_lower
        assert "postgresql" in req_lower
        assert data["seniority"] == "senior"

    def test_parse_jd_minimal_text(self, client: TestClient) -> None:
        payload = {"text": "Python Developer. Required: Python, Django."}
        response = client.post("/jd/parse", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"].startswith("jd-")
        req_lower = [s.lower() for s in data["required_skills"]]
        assert "python" in req_lower


# ── Tests: Applications ────────────────────────────────────────


class TestApplications:
    def test_list_applications_empty(self, client: TestClient) -> None:
        response = client.get("/applications")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_applications_after_jd_parse(self, client: TestClient) -> None:
        client.post("/jd/parse", json={"text": SAMPLE_JD})
        response = client.get("/applications")
        assert response.status_code == 200
        apps = response.json()
        assert len(apps) == 1

    def test_get_application(self, client: TestClient) -> None:
        parse_resp = client.post("/jd/parse", json={"text": SAMPLE_JD, "company": "Acme"})
        jd_id = parse_resp.json()["job_id"]

        get_resp = client.get(f"/applications/{jd_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["company"] == "Acme"

    def test_get_nonexistent_application(self, client: TestClient) -> None:
        response = client.get("/applications/noexist")
        assert response.status_code == 404

    def test_delete_application(self, client: TestClient) -> None:
        parse_resp = client.post("/jd/parse", json={"text": SAMPLE_JD})
        jd_id = parse_resp.json()["job_id"]

        del_resp = client.delete(f"/applications/{jd_id}")
        assert del_resp.status_code == 200
        assert del_resp.json() == {"status": "deleted", "app_id": jd_id}

        get_resp = client.get(f"/applications/{jd_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_application(self, client: TestClient) -> None:
        response = client.delete("/applications/noexist")
        assert response.status_code == 404


# ── Tests: Tailor ──────────────────────────────────────────────


class TestTailor:
    def test_tailor_fails_unapproved_profile(self, client: TestClient) -> None:
        profile = _make_unapproved_profile("unapproved-profile")
        client.post("/profiles", json=profile)

        parse_resp = client.post("/jd/parse", json={"text": SAMPLE_JD})
        jd_id = parse_resp.json()["job_id"]

        tailor_resp = client.post(
            "/tailor",
            json={"profile_id": "unapproved-profile", "jd_id": jd_id},
        )
        assert tailor_resp.status_code == 400
        detail = tailor_resp.json()["detail"]
        assert "not been approved" in detail.lower()

    def test_tailor_succeeds_with_approved_profile(self, client: TestClient) -> None:
        profile = _make_approved_profile("approved-profile")
        client.post("/profiles", json=profile)

        parse_resp = client.post("/jd/parse", json={"text": SAMPLE_JD})
        jd_id = parse_resp.json()["job_id"]

        tailor_resp = client.post(
            "/tailor",
            json={"profile_id": "approved-profile", "jd_id": jd_id, "mode": "conservative"},
        )
        assert tailor_resp.status_code == 200
        data = tailor_resp.json()
        assert "plan" in data
        assert "generated_bullets" in data
        assert "validation" in data
        assert data["plan"]["template_id"] == "ats-modern"
        assert len(data["generated_bullets"]) > 0
        assert data["validation"]["status"] in ("passed", "passed_with_warnings")

    def test_tailor_profile_not_found(self, client: TestClient) -> None:
        parse_resp = client.post("/jd/parse", json={"text": SAMPLE_JD})
        jd_id = parse_resp.json()["job_id"]

        tailor_resp = client.post(
            "/tailor",
            json={"profile_id": "noexist", "jd_id": jd_id},
        )
        assert tailor_resp.status_code == 404

    def test_tailor_jd_not_found(self, client: TestClient) -> None:
        client.post("/profiles", json=_make_approved_profile("has-profile"))

        tailor_resp = client.post(
            "/tailor",
            json={"profile_id": "has-profile", "jd_id": "noexist"},
        )
        assert tailor_resp.status_code == 404


# ── Tests: Render ──────────────────────────────────────────────


class TestRender:
    def test_render_fails_unapproved_profile(self, client: TestClient) -> None:
        profile = _make_unapproved_profile("render-unapproved")
        client.post("/profiles", json=profile)

        parse_resp = client.post("/jd/parse", json={"text": SAMPLE_JD})
        jd_id = parse_resp.json()["job_id"]

        render_resp = client.post(
            "/render",
            json={"profile_id": "render-unapproved", "jd_id": jd_id},
        )
        assert render_resp.status_code == 400
        assert "not been approved" in render_resp.json()["detail"].lower()

    def test_render_succeeds_with_approved_profile(self, client: TestClient) -> None:
        profile = _make_approved_profile("render-approved")
        client.post("/profiles", json=profile)

        parse_resp = client.post("/jd/parse", json={"text": SAMPLE_JD})
        jd_id = parse_resp.json()["job_id"]

        render_resp = client.post(
            "/render",
            json={"profile_id": "render-approved", "jd_id": jd_id},
        )
        assert render_resp.status_code == 200
        data = render_resp.json()
        assert "tex" in data
        assert len(data["tex"]) > 0

    def test_render_profile_not_found(self, client: TestClient) -> None:
        parse_resp = client.post("/jd/parse", json={"text": SAMPLE_JD})
        jd_id = parse_resp.json()["job_id"]

        render_resp = client.post(
            "/render",
            json={"profile_id": "noexist", "jd_id": jd_id},
        )
        assert render_resp.status_code == 404


# ── Tests: Config ──────────────────────────────────────────────


class TestConfig:
    def test_get_default_config(self, client: TestClient) -> None:
        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data

    def test_update_and_get_config(self, client: TestClient) -> None:
        new_config = {"version": "1.0.0", "theme": "dark", "language": "en"}
        put_resp = client.put("/config", json=new_config)
        assert put_resp.status_code == 200
        assert put_resp.json() == {"status": "saved"}

        get_resp = client.get("/config")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["theme"] == "dark"
        assert data["language"] == "en"


# ── Tests: Full Workflow ───────────────────────────────────────


class TestFullWorkflow:
    def test_full_workflow(self, client: TestClient) -> None:
        # 1. Save approved profile
        profile = _make_approved_profile("workflow-profile")
        save_resp = client.post("/profiles", json=profile)
        assert save_resp.status_code == 200
        assert save_resp.json()["status"] == "saved"

        # 2. Parse JD
        parse_resp = client.post(
            "/jd/parse",
            json={"text": SAMPLE_JD, "company": "Acme Corp", "role_title": "Senior Backend Engineer"},
        )
        assert parse_resp.status_code == 200
        jd_id = parse_resp.json()["job_id"]
        assert "Senior Backend Engineer" == parse_resp.json()["role_title"]

        # 3. Tailor
        tailor_resp = client.post(
            "/tailor",
            json={"profile_id": "workflow-profile", "jd_id": jd_id},
        )
        assert tailor_resp.status_code == 200
        tailor_data = tailor_resp.json()
        assert "plan" in tailor_data
        assert "generated_bullets" in tailor_data
        assert "validation" in tailor_data
        assert len(tailor_data["generated_bullets"]) > 0

        # 4. Render
        render_resp = client.post(
            "/render",
            json={"profile_id": "workflow-profile", "jd_id": jd_id},
        )
        assert render_resp.status_code == 200
        tex = render_resp.json()["tex"]
        assert "\\documentclass" in tex or "\\section" in tex or "\\begin{" in tex
