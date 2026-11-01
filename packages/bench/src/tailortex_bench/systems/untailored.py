"""Untailored control."""

from __future__ import annotations

from typing import Any

from tailortex_bench.corpus import Case


class Untailored:
    id = "untailored"
    kind = "untailored"

    def run(self, case: Case) -> dict[str, Any]:
        return {"text": case.resume, "model": None, "version": "corpus-v0"}
