"""Synthetic benchmark command line."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import typer

from tailortex_bench import __version__
from tailortex_bench.audit.match import audit_output
from tailortex_bench.calibration import DEFAULT_SET, calibrate
from tailortex_bench.corpus import (
    DEFAULT_CORPUS,
    ROOT,
    Case,
    CorpusError,
    load_corpus,
    load_json,
    validate_document,
)
from tailortex_bench.metrics import aggregate, case_metrics
from tailortex_bench.report import markdown, read_results, sidecar, write_json
from tailortex_bench.systems import External, PromptBaseline, TailorTex, Untailored
from tailortex_bench.systems.base import System
from tailortex_bench.systems.prompt_baseline import ProviderError
from tailortex_bench.systems.tailortex_system import product_commit

app = typer.Typer(no_args_is_help=True)


def _failure(message: str, code: int) -> None:
    typer.echo(message, err=True)
    raise typer.Exit(code)


def _calibration() -> dict[str, Any]:
    result = calibrate()
    overall = result["overall"]
    if overall["precision"] < 0.90 or overall["recall"] < 0.90:
        _failure("Auditor calibration below 0.90; inspect confusion table", 2)
    return result


@app.command("validate-corpus")
def validate_corpus(corpus: Path = typer.Option(DEFAULT_CORPUS, "--corpus")) -> None:
    try:
        manifest, cases = load_corpus(corpus)
    except (CorpusError, OSError) as exc:
        _failure(str(exc), 2)
    typer.echo(f"Valid corpus {manifest['corpus_version']}: {len(cases)} cases")


def _tool_terms(cases: list[Case]) -> list[str]:
    return sorted(
        {
            value
            for case in cases
            for atom in case.gold["atoms"]
            if atom["kind"] == "tool"
            for value in [atom["value"], *atom["aliases"]]
        },
        key=lambda value: (-len(value), value.casefold()),
    )


def _evaluate(
    outputs: Path, corpus: Path, out: Path, selected: set[str] | None = None
) -> dict[str, Any]:
    manifest, cases = load_corpus(corpus)
    previous = (
        load_json(outputs / "run-manifest.json")
        if (outputs / "run-manifest.json").is_file()
        else {}
    )
    status = dict(previous.get("statuses", {}))
    reproducibility = previous.get("reproducible", {})
    system_rows: dict[str, list[tuple[dict[str, Any], dict[str, int]]]] = {}
    systems: dict[str, dict[str, str]] = {}
    case_rows: list[dict[str, Any]] = []
    candidates: dict[str, list[dict[str, Any]]] = {}
    tool_terms = _tool_terms(cases)
    for case in cases:
        if selected is not None and case.key not in selected:
            continue
        path = outputs / f"{case.key}.json"
        if not path.is_file():
            status.setdefault(case.key, "missing")
            continue
        output = load_json(path)
        validate_document("system-output", output)
        if output["case"] != {"dossier_id": case.dossier_id, "job_id": case.job_id}:
            raise CorpusError(f"Wrong case in {path}")
        system_id = output["system_id"]
        systems[system_id] = {
            "system_id": system_id,
            "kind": output["kind"],
            "version": output["version"],
        }
        status[case.key] = "ok"
        audit, uncertain = audit_output(
            output["text"],
            case.gold,
            case.gold["jobs"][case.job_id],
            tool_terms,
            case.dossier_id,
            case.job_id,
            system_id,
            case.resume,
        )
        validate_document("claim-audit", audit)
        write_json(outputs / f"{case.key}.audit.json", audit)
        candidates[case.key] = uncertain
        metrics, counts = case_metrics(
            output["text"],
            case.resume,
            audit,
            case.gold,
            case.job_id,
            reproducibility.get(case.key),
            output["run_metadata"]["observed_pages"],
            output["run_metadata"]["max_pages"],
        )
        case_rows.append({"case": output["case"], "system_id": system_id, "metrics": metrics})
        system_rows.setdefault(system_id, []).append((metrics, counts))
    result = {
        "protocol_version": manifest["protocol_version"],
        "corpus_version": manifest["corpus_version"],
        "generated_by": f"tailortex-bench {__version__}",
        "systems": [systems[key] for key in sorted(systems)],
        "cases": sorted(
            case_rows,
            key=lambda row: (row["system_id"], row["case"]["dossier_id"], row["case"]["job_id"]),
        ),
        "aggregate": {key: aggregate(system_rows[key]) for key in sorted(system_rows)},
    }
    validate_document("results", result)
    write_json(out, result)
    metadata = {
        "commands": previous.get("commands", [" ".join(sys.argv)]),
        "calibration": _calibration(),
        "product_commits": previous.get("product_commits", {}),
        "statuses": dict(sorted(status.items())),
        "candidates": dict(sorted(candidates.items())),
    }
    write_json(sidecar(out), metadata)
    return result


@app.command()
def run(
    system: str = typer.Option(..., "--system"),
    corpus: Path = typer.Option(DEFAULT_CORPUS, "--corpus"),
    out: Path | None = typer.Option(None, "--out"),
    cases: str | None = typer.Option(None, "--cases"),
    repeat: int = typer.Option(1, "--repeat", min=1),
    provider: str = typer.Option("mock", "--provider"),
    model: str | None = typer.Option(None, "--model"),
    name: str | None = typer.Option(None, "--name"),
    outputs_dir: Path | None = typer.Option(None, "--outputs-dir"),
) -> None:
    try:
        _, all_cases = load_corpus(corpus)
        selected = (
            set(part.strip().replace(":", "__") for part in cases.split(",")) if cases else None
        )
        if selected is not None:
            unknown = selected - {case.key for case in all_cases}
            if unknown:
                raise CorpusError(f"Unknown cases: {', '.join(sorted(unknown))}")
        if system == "untailored":
            adapter: System = Untailored()
        elif system == "tailortex":
            adapter = TailorTex()
        elif system == "prompt-baseline":
            adapter = PromptBaseline(provider, model)
        elif system == "external":
            if not name or not outputs_dir:
                raise CorpusError("external requires --name and --outputs-dir")
            if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name):
                raise CorpusError("--name must contain lowercase letters, digits, _ or -")
            adapter = External(name, outputs_dir)
        else:
            raise CorpusError(f"Unknown system: {system}")
        destination = out or ROOT / "benchmark/runs" / adapter.id
        destination.mkdir(parents=True, exist_ok=True)
        statuses: dict[str, str] = {}
        reproducibility: dict[str, float | None] = {}
        for case in all_cases:
            if selected is not None and case.key not in selected:
                continue
            outputs = [adapter.run(case) for _ in range(repeat)]
            if outputs[0] is None:
                statuses[case.key] = "missing"
                (destination / f"{case.key}.json").unlink(missing_ok=True)
                continue
            data = outputs[0]
            assert data is not None
            statuses[case.key] = "ok"
            reproducibility[case.key] = (
                float(
                    all(
                        item is not None
                        and item["text"].encode("utf-8") == data["text"].encode("utf-8")
                        for item in outputs[1:]
                    )
                )
                if repeat > 1
                else None
            )
            output = {
                "system_id": adapter.id,
                "kind": adapter.kind,
                "version": data["version"],
                "model": data["model"],
                "case": {"dossier_id": case.dossier_id, "job_id": case.job_id},
                "text": data["text"],
                "artifact_path": None,
                "run_metadata": {
                    "run_id": f"{adapter.id}-{case.key}",
                    "run_date": date.today().isoformat(),
                    "max_pages": None,
                    "observed_pages": data.get("observed_pages"),
                },
            }
            validate_document("system-output", output)
            write_json(destination / f"{case.key}.json", output)
        meta = {
            "commands": [" ".join(sys.argv)],
            "statuses": statuses,
            "reproducible": reproducibility,
            "product_commits": ({"tailortex": product_commit()} if system == "tailortex" else {}),
        }
        write_json(destination / "run-manifest.json", meta)
        result = _evaluate(destination, corpus, destination / "results.json", selected)
        typer.echo(f"Wrote {len(result['cases'])} scored cases to {destination / 'results.json'}")
    except ProviderError as exc:
        _failure(str(exc), 4)
    except (CorpusError, ValueError) as exc:
        _failure(str(exc), 2)
    except (OSError, KeyError) as exc:
        _failure(str(exc), 1)


@app.command()
def audit(
    outputs: Path = typer.Option(..., "--outputs"),
    corpus: Path = typer.Option(DEFAULT_CORPUS, "--corpus"),
    out: Path | None = typer.Option(None, "--out"),
) -> None:
    try:
        result = _evaluate(outputs, corpus, out or outputs / "results.json")
        typer.echo(f"Audited {len(result['cases'])} cases")
    except (CorpusError, ValueError) as exc:
        _failure(str(exc), 2)


@app.command()
def report(
    results: list[Path] = typer.Option(..., "--results"),
    format: str = typer.Option("md", "--format"),
    out: Path | None = typer.Option(None, "--out"),
) -> None:
    try:
        merged, metadata = read_results(results)
        if format == "md":
            content = markdown(merged, metadata)
            if out:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(content, encoding="utf-8")
            else:
                typer.echo(content)
        elif format == "json":
            if out:
                write_json(out, merged)
                write_json(sidecar(out), metadata)
            else:
                typer.echo(json.dumps(merged, indent=2, sort_keys=True))
        else:
            raise ValueError("--format must be md or json")
    except (CorpusError, ValueError, OSError) as exc:
        _failure(str(exc), 2)


@app.command("calibrate-auditor")
def calibrate_auditor(set_path: Path = typer.Option(DEFAULT_SET, "--set")) -> None:
    try:
        result = calibrate(set_path)
    except (CorpusError, ValueError) as exc:
        _failure(str(exc), 2)
    typer.echo("Kind | TP | FP | FN | Precision | Recall")
    for kind, row in [*sorted(result["by_kind"].items()), ("overall", result["overall"])]:
        precision = f"{row['precision']:.3f}" if row["precision"] is not None else "—"
        recall = f"{row['recall']:.3f}" if row["recall"] is not None else "—"
        typer.echo(f"{kind} | {row['tp']} | {row['fp']} | {row['fn']} | {precision} | {recall}")
    if result["confusion"]:
        typer.echo("Confusion table:")
        for row in result["confusion"]:
            typer.echo(f"{row['id']}: expected={row['expected']} predicted={row['predicted']}")
    if result["overall"]["precision"] < 0.90 or result["overall"]["recall"] < 0.90:
        raise typer.Exit(2)


if __name__ == "__main__":
    app()
