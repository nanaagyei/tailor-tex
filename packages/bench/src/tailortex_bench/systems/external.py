"""Read manually produced external resumes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tailortex.parsers.extractors import extract_text

from tailortex_bench.corpus import Case


class External:
    kind = "external"

    def __init__(self, name: str, outputs_dir: Path) -> None:
        self.id = name
        self.outputs_dir = outputs_dir

    def run(self, case: Case) -> dict[str, Any] | None:
        candidates = [
            self.outputs_dir / f"{case.key}.{suffix}" for suffix in ("txt", "md", "pdf", "docx")
        ]
        found = [path for path in candidates if path.is_file()]
        if not found:
            return None
        if len(found) > 1:
            raise ValueError(f"Multiple external outputs for {case.key}: {found}")
        extracted = extract_text(found[0])
        return {
            "text": extracted.text,
            "model": None,
            "version": "manual-v1",
            "observed_pages": extracted.page_count,
            "artifact_path": str(found[0].resolve()),
        }
