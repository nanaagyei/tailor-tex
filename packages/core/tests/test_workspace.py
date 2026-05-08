"""Tests for the workspace manager."""

import json

import pytest

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
        assert workspace.applications_dir.is_dir()
        assert workspace.exports_dir.is_dir()

    def test_init_creates_config(self, workspace):
        assert workspace.config_path.exists()
        config = json.loads(workspace.config_path.read_text())
        assert config["version"] == "1.0.0"

    def test_init_idempotent(self, workspace):
        workspace.init()  # Call again — should not error
        assert workspace.exists()

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

    def test_export_path_traversal_blocked(self, workspace):
        with pytest.raises(WorkspaceError, match="traversal"):
            workspace.save_export("app-001", "../../evil.tex", "bad")

    def test_safe_names_work(self, workspace, sample_profile):
        """Normal names with hyphens and underscores should work fine."""
        workspace.save_profile(sample_profile)
        loaded = workspace.load_profile("test-profile")
        assert loaded.profile_id == "test-profile"
