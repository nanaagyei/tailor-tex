"""Independent hand-labelled auditor calibration."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tailortex_bench.audit.match import audit_output
from tailortex_bench.corpus import ROOT, load_json

DEFAULT_SET = ROOT / "benchmark/audit-calibration"
KINDS = ("metric", "tool", "scope", "organization", "title", "date", "credential", "outcome")


def calibrate(path: Path = DEFAULT_SET) -> dict[str, Any]:
    lines = load_json(path / "labels.json")["lines"]
    if (
        len(lines) < 40
        or sum(not item["expected"] for item in lines) < 10
        or sum(bool(item["expected"]) for item in lines) < 30
    ):
        raise ValueError("Calibration needs at least 40 lines: 10 clean and 30 planted")
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    confusion: list[dict[str, Any]] = []
    verdicts: set[str] = set()
    for item in lines:
        atoms = item["gold_atoms"]
        job = {
            "must_include": [],
            "jd_terms": item["job_terms"],
            "jd_only_terms": item["job_terms"],
            "canary": None,
        }
        gold = {"atoms": atoms, "jobs": {"cal": job}}
        audit, _ = audit_output(
            item["line"],
            gold,
            job,
            [atom["value"] for atom in atoms if atom["kind"] == "tool"],
            "cal",
            "cal",
            "cal",
        )
        predicted = Counter(
            (atom["kind"], atom["verdict"])
            for atom in audit["atoms"]
            if atom["verdict"] != "supported"
        )
        expected = Counter((atom["kind"], atom["verdict"]) for atom in item["expected"])
        verdicts.update(atom["verdict"] for atom in item["expected"])
        for kind, verdict in set(predicted) | set(expected):
            matched = min(predicted[(kind, verdict)], expected[(kind, verdict)])
            counts[kind]["tp"] += matched
            counts[kind]["fp"] += predicted[(kind, verdict)] - matched
            counts[kind]["fn"] += expected[(kind, verdict)] - matched
        if predicted != expected:
            confusion.append(
                {
                    "id": item["id"],
                    "expected": sorted(expected.elements()),
                    "predicted": sorted(predicted.elements()),
                }
            )
    if verdicts != {"unsupported", "misattributed", "inflated"}:
        raise ValueError("Calibration must include all three unsupported verdicts")
    by_kind = {}
    for kind in KINDS:
        c = counts[kind]
        by_kind[kind] = {
            "precision": c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else None,
            "recall": c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else None,
            **{name: c[name] for name in ("tp", "fp", "fn")},
        }
    total = sum((counts[kind] for kind in KINDS), Counter())
    overall = {
        "precision": total["tp"] / (total["tp"] + total["fp"]) if total["tp"] + total["fp"] else 0,
        "recall": total["tp"] / (total["tp"] + total["fn"]) if total["tp"] + total["fn"] else 0,
        **{name: total[name] for name in ("tp", "fp", "fn")},
    }
    return {"lines": len(lines), "by_kind": by_kind, "overall": overall, "confusion": confusion}
