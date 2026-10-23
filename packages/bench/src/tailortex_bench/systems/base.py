"""System adapter contract."""

from __future__ import annotations

from typing import Any, Protocol

from tailortex_bench.corpus import Case

SystemOutput = dict[str, Any]


class System(Protocol):
    id: str
    kind: str

    def run(self, case: Case) -> SystemOutput | None: ...
