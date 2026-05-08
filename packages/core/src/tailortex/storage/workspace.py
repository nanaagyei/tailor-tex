"""Workspace manager — local file storage for profiles, applications, and config.

The workspace is a directory (default: ~/.tailortex/) containing:
  profiles/       — canonical profiles (JSON)
  applications/   — tailoring applications (JSON)
  config.json     — workspace settings
  exports/        — rendered artifacts
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from tailortex.schemas.profile import CanonicalProfile
from tailortex.schemas.validation import ValidationReport

T = TypeVar("T", bound=BaseModel)

DEFAULT_WORKSPACE = Path.home() / ".tailortex"

_SUBDIRS = ("profiles", "applications", "exports")


class WorkspaceError(Exception):
    """Raised for workspace-related errors."""


class Workspace:
    """Manages the local workspace directory for TailorTex."""

    def __init__(self, root: str | Path | None = None) -> None:
        self._root = Path(root) if root else DEFAULT_WORKSPACE

    @property
    def root(self) -> Path:
        return self._root

    @property
    def profiles_dir(self) -> Path:
        return self._root / "profiles"

    @property
    def applications_dir(self) -> Path:
        return self._root / "applications"

    @property
    def exports_dir(self) -> Path:
        return self._root / "exports"

    @property
    def config_path(self) -> Path:
        return self._root / "config.json"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def init(self) -> None:
        """Create workspace directory structure if it doesn't exist."""
        self._root.mkdir(parents=True, exist_ok=True)
        for subdir in _SUBDIRS:
            (self._root / subdir).mkdir(exist_ok=True)
        if not self.config_path.exists():
            self._atomic_write(self.config_path, json.dumps({"version": "1.0.0"}, indent=2))

    def exists(self) -> bool:
        return self._root.is_dir()

    # ------------------------------------------------------------------
    # Path safety
    # ------------------------------------------------------------------

    def _safe_path(self, base: Path, name: str) -> Path:
        """Resolve a path and verify it stays within the base directory.

        Prevents path traversal attacks (e.g. ../../etc/passwd).
        """
        resolved = (base / name).resolve()
        base_resolved = base.resolve()
        if not str(resolved).startswith(str(base_resolved) + os.sep) and resolved != base_resolved:
            raise WorkspaceError(f"Path traversal blocked: {name!r} escapes {base}")
        return resolved

    # ------------------------------------------------------------------
    # Atomic file writes
    # ------------------------------------------------------------------

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        """Write to a temp file then rename — prevents partial writes."""
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(content)
            os.replace(tmp, path)
        except BaseException:
            # Clean up temp file on failure
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    # ------------------------------------------------------------------
    # Generic model I/O
    # ------------------------------------------------------------------

    def _save_model(self, base: Path, name: str, model: BaseModel) -> Path:
        """Serialize a Pydantic model to JSON in the given subdirectory."""
        path = self._safe_path(base, f"{name}.json")
        self._atomic_write(path, model.model_dump_json(indent=2))
        return path

    def _load_model(self, base: Path, name: str, model_cls: type[T]) -> T:
        """Deserialize a Pydantic model from JSON."""
        path = self._safe_path(base, f"{name}.json")
        if not path.exists():
            raise WorkspaceError(f"Not found: {path}")
        raw = path.read_text(encoding="utf-8")
        return model_cls.model_validate_json(raw)

    def _list_items(self, base: Path) -> list[str]:
        """List item names (without .json extension) in a subdirectory."""
        if not base.is_dir():
            return []
        return sorted(p.stem for p in base.glob("*.json"))

    def _delete_item(self, base: Path, name: str) -> None:
        """Delete a JSON item from a subdirectory."""
        path = self._safe_path(base, f"{name}.json")
        if not path.exists():
            raise WorkspaceError(f"Not found: {path}")
        path.unlink()

    # ------------------------------------------------------------------
    # Profile operations
    # ------------------------------------------------------------------

    def save_profile(self, profile: CanonicalProfile) -> Path:
        return self._save_model(self.profiles_dir, profile.profile_id, profile)

    def load_profile(self, profile_id: str = "default") -> CanonicalProfile:
        return self._load_model(self.profiles_dir, profile_id, CanonicalProfile)

    def list_profiles(self) -> list[str]:
        return self._list_items(self.profiles_dir)

    def delete_profile(self, profile_id: str) -> None:
        self._delete_item(self.profiles_dir, profile_id)

    # ------------------------------------------------------------------
    # Application operations (stores resume plans, bullets, reports)
    # ------------------------------------------------------------------

    def save_application(self, app_id: str, data: dict) -> Path:
        """Save an application bundle as JSON."""
        path = self._safe_path(self.applications_dir, f"{app_id}.json")
        content = json.dumps(data, indent=2, default=str)
        self._atomic_write(path, content)
        return path

    def load_application(self, app_id: str) -> dict:
        path = self._safe_path(self.applications_dir, f"{app_id}.json")
        if not path.exists():
            raise WorkspaceError(f"Application not found: {app_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def list_applications(self) -> list[str]:
        return self._list_items(self.applications_dir)

    def delete_application(self, app_id: str) -> None:
        self._delete_item(self.applications_dir, app_id)

    # ------------------------------------------------------------------
    # Config operations
    # ------------------------------------------------------------------

    def load_config(self) -> dict:
        if not self.config_path.exists():
            return {"version": "1.0.0"}
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    def save_config(self, config: dict) -> None:
        self._atomic_write(self.config_path, json.dumps(config, indent=2))

    # ------------------------------------------------------------------
    # Export operations
    # ------------------------------------------------------------------

    def save_export(self, app_id: str, filename: str, content: str) -> Path:
        """Save an export artifact (e.g. .tex file) under exports/<app_id>/."""
        export_dir = self.exports_dir / app_id
        path = self._safe_path(export_dir, filename)
        self._atomic_write(path, content)
        return path

    def list_exports(self, app_id: str) -> list[str]:
        export_dir = self.exports_dir / app_id
        if not export_dir.is_dir():
            return []
        return sorted(p.name for p in export_dir.iterdir() if p.is_file())
