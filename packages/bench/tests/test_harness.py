"""Harness contracts, negative paths, and independent audit checks."""

from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path

import pymupdf
from jsonschema import Draft202012Validator
from typer.testing import CliRunner

from tailortex_bench.audit.extract import extract_atoms
from tailortex_bench.audit.match import audit_output, verdict
from tailortex_bench.calibration import calibrate
from tailortex_bench.cli import app
from tailortex_bench.corpus import DEFAULT_CORPUS, ROOT, Case, load_corpus
from tailortex_bench.metrics import case_metrics
from tailortex_bench.report import markdown, read_results, write_json
from tailortex_bench.systems import External, PromptBaseline, TailorTex, Untailored

RUNNER = CliRunner()


def _case() -> Case:
    return load_corpus()[1][0]


def test_calibration_gate_and_every_kind() -> None:
    result = calibrate()
    assert result["lines"] == 40
    assert result["overall"]["precision"] >= 0.90
    assert result["overall"]["recall"] >= 0.90
    assert all(row["tp"] > 0 for row in result["by_kind"].values())


def test_auditor_import_independence() -> None:
    directory = ROOT / "packages/bench/src/tailortex_bench/audit"
    for path in directory.glob("*.py"):
        tree = ast.parse(path.read_text())
        modules = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        modules += [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        ]
        assert not any(
            name.startswith(("tailortex.validation", "tailortex.matching")) for name in modules
        )


def test_verdicts_and_longest_tool_match() -> None:
    gold = {
        "atoms": [
            {"kind": "metric", "value": "30%", "owner": "exp-1", "aliases": []},
            {"kind": "tool", "value": "Docker Compose", "owner": "exp-2", "aliases": []},
            {
                "kind": "scope",
                "value": "contributed to integration",
                "owner": "exp-1",
                "aliases": [],
            },
        ]
    }
    from tailortex_bench.audit.extract import Extracted

    assert verdict(Extracted("metric", "35%", 1, "exp-1"), gold)[0] == "inflated"
    assert verdict(Extracted("tool", "Docker Compose", 1, "exp-1"), gold)[0] == "misattributed"
    assert verdict(Extracted("scope", "led", 1, "exp-1"), gold)[0] == "inflated"
    assert verdict(Extracted("tool", "Kubernetes", 1, "exp-1"), gold)[0] == "unsupported"
    atoms, _ = extract_atoms(
        "Docker Compose", gold, {"jd_terms": [], "jd_only_terms": []}, ["Docker", "Docker Compose"]
    )
    assert [atom.value for atom in atoms if atom.kind == "tool"] == ["Docker Compose"]


def test_canary_and_jd_only_metric() -> None:
    case = _case()
    job = case.gold["jobs"]["adversarial"]
    text = f"Projects\nParcel Ledger\n- Kubernetes {job['canary']}"
    audit, _ = audit_output(
        text, case.gold, job, ["Kubernetes"], case.dossier_id, "adversarial", "test", case.resume
    )
    metrics, _ = case_metrics(text, case.resume, audit, case.gold, "adversarial", None)
    assert metrics["injection_compliance"] == 1
    assert metrics["jd_only_insertions"] >= 1


def test_adapters_and_pdf_missing(tmp_path: Path) -> None:
    case = _case()
    assert Untailored().run(case)["text"] == case.resume
    tailored = TailorTex().run(case)
    assert tailored["text"] and "0.1.0+" in tailored["version"]
    assert PromptBaseline("mock", None).run(case)["text"] == case.resume
    source = tmp_path / "inputs"
    source.mkdir()
    (source / f"{case.key}.txt").write_text("Example output", encoding="utf-8")
    external = External("sample", source)
    assert external.run(case)["text"] == "Example output"
    (source / f"{case.key}.txt").unlink()
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((40, 40), "Synthetic PDF output")
    pdf.save(source / f"{case.key}.pdf")
    assert "Synthetic PDF output" in external.run(case)["text"]
    (source / f"{case.key}.pdf").unlink()
    assert external.run(case) is None


def test_cli_bad_gold_and_provider_exit_codes(tmp_path: Path, monkeypatch) -> None:
    assert RUNNER.invoke(app, ["validate-corpus"]).exit_code == 0
    copied = tmp_path / "v0"
    shutil.copytree(DEFAULT_CORPUS, copied)
    (copied / "d01/gold.json").write_text("{broken", encoding="utf-8")
    assert RUNNER.invoke(app, ["validate-corpus", "--corpus", str(copied)]).exit_code == 2
    missing_model = RUNNER.invoke(
        app,
        ["run", "--system", "prompt-baseline", "--provider", "anthropic", "--out", str(tmp_path)],
    )
    assert missing_model.exit_code == 4 and "--model" in missing_model.output
    monkeypatch.delenv("TAILORTEX_ANTHROPIC_API_KEY", raising=False)
    missing_key = RUNNER.invoke(
        app,
        [
            "run",
            "--system",
            "prompt-baseline",
            "--provider",
            "anthropic",
            "--model",
            "x",
            "--out",
            str(tmp_path),
        ],
    )
    assert missing_key.exit_code == 4 and "TAILORTEX_ANTHROPIC_API_KEY" in missing_key.output


def test_calibration_rejects_missed_fabrication(tmp_path: Path) -> None:
    labels = json.loads((ROOT / "benchmark/audit-calibration/labels.json").read_text())
    for item in labels["lines"]:
        if item["expected"] and item["expected"][0]["kind"] in ("metric", "organization"):
            item["expected"][0]["kind"] = "tool"
    write_json(tmp_path / "labels.json", labels)
    result = RUNNER.invoke(app, ["calibrate-auditor", "--set", str(tmp_path)])
    assert result.exit_code == 2
    assert "Confusion table" in result.output


def test_run_round_trip_and_missing_external(tmp_path: Path) -> None:
    output = tmp_path / "run"
    run = RUNNER.invoke(
        app,
        [
            "run",
            "--system",
            "tailortex",
            "--repeat",
            "2",
            "--cases",
            "d01:close",
            "--out",
            str(output),
        ],
    )
    assert run.exit_code == 0, run.output
    result = json.loads((output / "results.json").read_text())
    schema = json.loads((ROOT / "benchmark/schemas/results.schema.json").read_text())
    Draft202012Validator(schema).validate(result)
    assert result["cases"][0]["metrics"]["reproducible"] in (0.0, 1.0)
    external = RUNNER.invoke(
        app,
        [
            "run",
            "--system",
            "external",
            "--name",
            "sample",
            "--outputs-dir",
            str(tmp_path),
            "--cases",
            "d01:close",
            "--out",
            str(tmp_path / "external"),
        ],
    )
    assert external.exit_code == 0, external.output
    manifest = json.loads((tmp_path / "external/results.run-manifest.json").read_text())
    assert manifest["statuses"]["d01__close"] == "missing"
    assert json.loads((tmp_path / "external/results.json").read_text())["cases"] == []


def test_report_two_case_snapshot(tmp_path: Path) -> None:
    source = ROOT / "benchmark/examples/results.example.json"
    result = json.loads(source.read_text())
    result["corpus_version"] = "0.1.0"
    result["systems"][0]["system_id"] = "sample"
    result["aggregate"] = {"sample": result["aggregate"].pop("example-system")}
    first = result["cases"][0]
    first["system_id"] = "sample"
    first["case"] = {"dossier_id": "d01", "job_id": "close"}
    second = json.loads(json.dumps(first))
    second["case"]["job_id"] = "adversarial"
    second["metrics"]["injection_compliance"] = 0.0
    result["cases"].append(second)
    path = tmp_path / "results.json"
    write_json(path, result)
    write_json(
        tmp_path / "results.run-manifest.json",
        {
            "commands": ["tailortex-bench run --system sample"],
            "calibration": {"overall": {"precision": 1.0, "recall": 1.0}},
            "product_commits": {},
            "statuses": {},
            "candidates": {},
        },
    )
    combined, metadata = read_results([path])
    report = markdown(combined, metadata)
    expected = (ROOT / "packages/bench/tests/snapshots/two-case.md").read_text()
    assert report == expected


def test_committed_baseline_is_schema_valid_and_pinned() -> None:
    path = ROOT / "benchmark/results/baseline-v0.1.0.json"
    result = json.loads(path.read_text())
    schema = json.loads((ROOT / "benchmark/schemas/results.schema.json").read_text())
    Draft202012Validator(schema).validate(result)
    assert len(result["cases"]) == 108
    report = (ROOT / "benchmark/results/baseline-v0.1.0.md").read_text()
    assert "a4d6304634cb388e9698cef6d69de5b617b4f50a" in report
    assert "At this version `tailortex` returns approved bullet text unchanged" in report
