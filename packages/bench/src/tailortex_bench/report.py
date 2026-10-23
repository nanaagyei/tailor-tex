"""Schema-valid result merge and human-readable reporting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tailortex_bench.corpus import ROOT, load_json, validate_document
from tailortex_bench.metrics import METRIC_NAMES

AUTOMATED = METRIC_NAMES[:10]


def sidecar(path: Path) -> Path:
    return path.with_name(path.stem + ".run-manifest.json")


def read_results(paths: list[Path]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not paths:
        raise ValueError("Provide at least one --results file")
    documents = [load_json(path) for path in paths]
    for doc in documents:
        validate_document("results", doc)
    versions = {(doc["protocol_version"], doc["corpus_version"]) for doc in documents}
    if len(versions) != 1:
        raise ValueError("Cannot combine results from different protocol or corpus versions")
    systems = {item["system_id"]: item for doc in documents for item in doc["systems"]}
    cases = [row for doc in documents for row in doc["cases"]]
    if len(
        {(row["system_id"], row["case"]["dossier_id"], row["case"]["job_id"]) for row in cases}
    ) != len(cases):
        raise ValueError("Duplicate system/case results")
    aggregate = {system: data for doc in documents for system, data in doc["aggregate"].items()}
    merged = {
        "protocol_version": documents[0]["protocol_version"],
        "corpus_version": documents[0]["corpus_version"],
        "generated_by": "tailortex-bench 0.1.0",
        "systems": [systems[key] for key in sorted(systems)],
        "cases": sorted(
            cases,
            key=lambda row: (row["system_id"], row["case"]["dossier_id"], row["case"]["job_id"]),
        ),
        "aggregate": dict(sorted(aggregate.items())),
    }
    validate_document("results", merged)
    manifests = [load_json(sidecar(path)) for path in paths]
    metadata = {
        "commands": [command for manifest in manifests for command in manifest.get("commands", [])],
        "calibration": manifests[0].get("calibration"),
        "product_commits": {
            key: val
            for manifest in manifests
            for key, val in manifest.get("product_commits", {}).items()
        },
        "statuses": {
            key: val for manifest in manifests for key, val in manifest.get("statuses", {}).items()
        },
        "candidates": {
            key: val
            for manifest in manifests
            for key, val in manifest.get("candidates", {}).items()
        },
    }
    return merged, metadata


def _cell(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _traps() -> dict[tuple[str, str], list[str]]:
    path = ROOT / "benchmark/corpus/v0/COVERAGE.md"
    text = path.read_text(encoding="utf-8").split("## Case \u00d7 trap matrix", 1)[1]
    result = {}
    for line in text.splitlines():
        if line.startswith("| d"):
            cells = [cell.strip() for cell in line.strip("| ").split("|")]
            result[(cells[0], cells[1])] = [] if cells[2] == "—" else cells[2].split(", ")
    return result


def markdown(results: dict[str, Any], metadata: dict[str, Any]) -> str:
    calibration = metadata.get("calibration") or {}
    overall = calibration.get("overall", {})
    commits = (
        ", ".join(
            f"{key}={value}" for key, value in sorted(metadata.get("product_commits", {}).items())
        )
        or "none"
    )
    lines = [
        "# TailorTex benchmark results",
        "",
        f"- Corpus version: {results['corpus_version']}",
        f"- Protocol version: {results['protocol_version']}",
        f"- Auditor calibration: precision {_cell(overall.get('precision'))}; "
        f"recall {_cell(overall.get('recall'))}",
        "- Commands: " + "; ".join(f"`{cmd}`" for cmd in metadata.get("commands", [])),
        "- Product commits: " + commits,
        "",
        "## Automated metrics",
        "",
    ]
    lines.append("| System | " + " | ".join(AUTOMATED) + " |")
    lines.append("| --- | " + " | ".join("---:" for _ in AUTOMATED) + " |")
    for system, values in sorted(results["aggregate"].items()):
        lines.append(
            "| " + system + " | " + " | ".join(_cell(values[name]) for name in AUTOMATED) + " |"
        )
    lines.extend(
        [
            "",
            "## Per-trap breakdown",
            "",
            "| System | Trap | Cases | Unsupported cases | "
            "JD-only insertions | Injection compliance |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    trap_map = _traps()
    for system in sorted(results["aggregate"]):
        rows = [row for row in results["cases"] if row["system_id"] == system]
        for trap in sorted(
            {
                trap
                for row in rows
                for trap in trap_map.get((row["case"]["dossier_id"], row["case"]["job_id"]), [])
            }
        ):
            selected = [
                row["metrics"]
                for row in rows
                if trap in trap_map.get((row["case"]["dossier_id"], row["case"]["job_id"]), [])
            ]
            attacked = [
                m["injection_compliance"] for m in selected if m["injection_compliance"] is not None
            ]
            lines.append(
                f"| {system} | {trap} | {len(selected)} | "
                f"{sum(m['cases_with_unsupported'] for m in selected):.0f} | "
                f"{sum(m['jd_only_insertions'] for m in selected)} | "
                f"{_cell(sum(attacked) / len(attacked) if attacked else None)} |"
            )
    missing = sorted(
        key for key, status in metadata.get("statuses", {}).items() if status == "missing"
    )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "Missing external cases: " + (", ".join(missing) if missing else "none") + ".",
        ]
    )
    return "\n".join(lines) + "\n"


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
