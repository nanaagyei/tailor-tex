"""Tests for the workspace manager."""

import json

import pytest

from tailortex.parsers.jd_parser import parse_jd_text
from tailortex.schemas.job import JDRecord
from tailortex.schemas.profile import CanonicalProfile, Owner
from tailortex.storage.workspace import Workspace, WorkspaceError


@pytest.fixture
def workspace(tmp_path):
    ws = Workspace(root=tmp_path / "test-workspace")
    ws.init()
    return ws


@pytest.fixture
def sample_profile():
    return CanonicalProfile(
        profile_id="test-profile",
        owner=Owner(full_name="Morgan Castillo", email="morgan@test.com"),
    )


class TestWorkspaceInit:
    def test_init_creates_directories(self, workspace):
        assert workspace.root.is_dir()
        assert workspace.profiles_dir.is_dir()
        assert workspace.drafts_dir.is_dir()
        assert workspace.jobs_dir.is_dir()
        assert workspace.applications_dir.is_dir()
        assert workspace.exports_dir.is_dir()

    def test_init_creates_config(self, workspace):
        assert workspace.config_path.exists()
        config = json.loads(workspace.config_path.read_text())
        assert config["version"] == "1.0.0"

    def test_init_idempotent(self, workspace):
        workspace.save_application("existing", {"status": "kept"})
        workspace.drafts_dir.rmdir()
        workspace.jobs_dir.rmdir()
        workspace.init()
        assert workspace.exists()
        assert workspace.drafts_dir.is_dir()
        assert workspace.jobs_dir.is_dir()
        assert workspace.load_application("existing") == {"status": "kept"}

    def test_exists_false_before_init(self, tmp_path):
        ws = Workspace(root=tmp_path / "nonexistent")
        assert not ws.exists()


class TestProfileCRUD:
    def test_save_and_load_profile(self, workspace, sample_profile):
        workspace.save_profile(sample_profile)
        loaded = workspace.load_profile("test-profile")
        assert loaded.owner.full_name == "Morgan Castillo"
        assert loaded.profile_id == "test-profile"

    def test_list_profiles(self, workspace, sample_profile):
        assert workspace.list_profiles() == []
        workspace.save_profile(sample_profile)
        assert workspace.list_profiles() == ["test-profile"]

    def test_delete_profile(self, workspace, sample_profile):
        workspace.save_profile(sample_profile)
        workspace.delete_profile("test-profile")
        assert workspace.list_profiles() == []

    def test_load_nonexistent_profile_raises(self, workspace):
        with pytest.raises(WorkspaceError, match="Not found"):
            workspace.load_profile("nonexistent")

    def test_delete_nonexistent_profile_raises(self, workspace):
        with pytest.raises(WorkspaceError, match="Not found"):
            workspace.delete_profile("nonexistent")

    def test_overwrite_profile(self, workspace, sample_profile):
        workspace.save_profile(sample_profile)
        sample_profile.owner.full_name = "Updated Name"
        workspace.save_profile(sample_profile)
        loaded = workspace.load_profile("test-profile")
        assert loaded.owner.full_name == "Updated Name"


class TestApplicationCRUD:
    def test_save_and_load_application(self, workspace):
        data = {"resume_id": "r1", "status": "draft"}
        workspace.save_application("app-001", data)
        loaded = workspace.load_application("app-001")
        assert loaded["resume_id"] == "r1"

    def test_list_applications(self, workspace):
        assert workspace.list_applications() == []
        workspace.save_application("app-001", {"status": "draft"})
        workspace.save_application("app-002", {"status": "complete"})
        assert workspace.list_applications() == ["app-001", "app-002"]

    def test_delete_application(self, workspace):
        workspace.save_application("app-001", {"status": "draft"})
        workspace.delete_application("app-001")
        assert workspace.list_applications() == []

    def test_load_nonexistent_application_raises(self, workspace):
        with pytest.raises(WorkspaceError, match="not found"):
            workspace.load_application("nonexistent")


class TestDraftCRUD:
    def test_round_trip_and_delete_source(self, workspace, sample_profile):
        path = workspace.save_draft(sample_profile, "Synthetic resume text")
        assert path == workspace.drafts_dir / "test-profile.json"
        assert workspace.has_draft("test-profile")
        assert workspace.list_drafts() == ["test-profile"]
        assert workspace.load_draft("test-profile") == sample_profile
        source = workspace.drafts_dir / "test-profile.source.txt"
        assert source.read_text() == "Synthetic resume text"
        workspace.delete_draft("test-profile")
        assert not path.exists()
        assert not source.exists()


class TestJobCRUD:
    def test_new_record_round_trip(self, workspace):
        result = parse_jd_text("QA Engineer requires Python", company="Example Systems")
        record = JDRecord(jd=result.jd, raw_text=result.raw_text, warnings=result.warnings)
        path = workspace.save_job(record)
        assert path == workspace.jobs_dir / f"{result.jd.job_id}.json"
        assert workspace.load_job(result.jd.job_id) == record
        assert workspace.list_jobs() == [result.jd.job_id]
        workspace.delete_job(result.jd.job_id)
        assert workspace.list_jobs() == []

    def test_legacy_nested_and_flat_shapes(self, workspace):
        nested = parse_jd_text("QA Engineer requires Python")
        flat = parse_jd_text("QA Engineer requires SQL")
        workspace.save_application(
            nested.jd.job_id,
            {
                "jd": nested.jd.model_dump(mode="json"),
                "raw_text": nested.raw_text,
                "warnings": nested.warnings,
            },
        )
        workspace.save_application(flat.jd.job_id, flat.jd.model_dump(mode="json"))
        workspace.save_application("unrelated", {"status": "draft"})
        workspace.save_application("broken", {"jd": {"job_id": "broken"}})
        assert workspace.load_job(nested.jd.job_id).raw_text == nested.raw_text
        flat_record = workspace.load_job(flat.jd.job_id)
        assert flat_record.jd == flat.jd
        assert flat_record.raw_text == ""
        assert flat_record.warnings == ["Legacy record: original job text not stored."]
        assert workspace.list_jobs() == sorted([nested.jd.job_id, flat.jd.job_id])

    def test_new_record_preferred_and_delete_removes_legacy_copy(self, workspace):
        result = parse_jd_text("QA Engineer requires Python")
        job_id = result.jd.job_id
        workspace.save_application(job_id, result.jd.model_dump(mode="json"))
        workspace.save_job(JDRecord(jd=result.jd, raw_text="new source"))
        assert workspace.load_job(job_id).raw_text == "new source"
        workspace.delete_job(job_id)
        assert not (workspace.jobs_dir / f"{job_id}.json").exists()
        assert not (workspace.applications_dir / f"{job_id}.json").exists()

    def test_delete_job_leaves_unrelated_application(self, workspace):
        workspace.save_application("app-001", {"status": "draft"})
        with pytest.raises(WorkspaceError, match="JD not found"):
            workspace.delete_job("app-001")
        assert workspace.load_application("app-001") == {"status": "draft"}


class TestConfig:
    def test_load_config(self, workspace):
        config = workspace.load_config()
        assert config["version"] == "1.0.0"

    def test_save_and_load_config(self, workspace):
        workspace.save_config({"version": "1.0.0", "llm_provider": "ollama"})
        config = workspace.load_config()
        assert config["llm_provider"] == "ollama"

    def test_load_config_default_when_missing(self, tmp_path):
        ws = Workspace(root=tmp_path / "no-config")
        config = ws.load_config()
        assert config["version"] == "1.0.0"


class TestExports:
    def test_save_and_list_exports(self, workspace):
        workspace.save_export("app-001", "resume.tex", "\\documentclass{article}")
        exports = workspace.list_exports("app-001")
        assert "resume.tex" in exports

    def test_list_exports_empty(self, workspace):
        assert workspace.list_exports("nonexistent") == []


class TestPathTraversal:
    def test_profile_path_traversal_blocked(self, workspace):
        with pytest.raises(WorkspaceError, match="traversal"):
            workspace.load_profile("../../etc/passwd")

    def test_application_path_traversal_blocked(self, workspace):
        with pytest.raises(WorkspaceError, match="traversal"):
            workspace.load_application("../../../secrets")

    def test_draft_path_traversal_blocked(self, workspace, sample_profile):
        sample_profile.profile_id = "../../outside"
        with pytest.raises(WorkspaceError, match="traversal"):
            workspace.save_draft(sample_profile, "text")
        with pytest.raises(WorkspaceError, match="traversal"):
            workspace.load_draft("../../outside")
        with pytest.raises(WorkspaceError, match="traversal"):
            workspace.delete_draft("../../outside")

    def test_job_path_traversal_blocked(self, workspace):
        result = parse_jd_text("QA Engineer requires Python")
        result.jd.job_id = "../../outside"
        with pytest.raises(WorkspaceError, match="traversal"):
            workspace.save_job(JDRecord(jd=result.jd, raw_text="text"))
        with pytest.raises(WorkspaceError, match="traversal"):
            workspace.load_job("../../outside")
        with pytest.raises(WorkspaceError, match="traversal"):
            workspace.delete_job("../../outside")

    def test_export_path_traversal_blocked(self, workspace):
        with pytest.raises(WorkspaceError, match="traversal"):
            workspace.save_export("app-001", "../../evil.tex", "bad")

    def test_safe_names_work(self, workspace, sample_profile):
        """Normal names with hyphens and underscores should work fine."""
        workspace.save_profile(sample_profile)
        loaded = workspace.load_profile("test-profile")
        assert loaded.profile_id == "test-profile"
