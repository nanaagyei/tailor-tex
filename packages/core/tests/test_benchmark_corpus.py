"""Contract checks for the publishable synthetic benchmark corpus."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tailortex.parsers.jd_parser import parse_jd_text
from tailortex.parsers.resume_parser import parse_resume_text

BENCHMARK = Path(__file__).resolve().parents[3] / "benchmark"
CORPUS = BENCHMARK / "corpus" / "v0"
IDS = tuple(f"d{i:02d}" for i in range(1, 13))
JOBS = ("close", "stretch", "adversarial")
EXPERIENCE_COUNTS = (0, 2, 3, 1, 2, 1, 2, 1, 1, 2, 1, 1)
TRAP_COUNTS = {
    "JD-only skill": 4,
    "Tempting metric": 4,
    "Scope inflation": 3,
    "Misattribution": 3,
    "Title pressure": 3,
    "Date pressure": 3,
    "Prompt injection": 12,
    "Credential pressure": 4,
}
TOOLS = (
    "Python", "SQLite", "Git", "pytest", "PostgreSQL", "Docker Compose", "Go",
    "OpenTelemetry", "TypeScript", "React", "CSS", "Vitest", "Playwright", "Figma",
    "pandas", "SQL", "scikit-learn", "Airflow", "dbt", "PyTorch", "Selenium",
    "Java", "JUnit", "Jenkins", "Terraform", "Docker", "GitHub Actions",
    "Prometheus", "Bash", "Kubernetes", "Grafana", "NumPy",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def table_rows(markdown: str, heading: str) -> list[list[str]]:
    section = markdown.split(heading, 1)[1].split("\n## ", 1)[0]
    return [
        [cell.strip() for cell in line.strip("| ").split("|")]
        for line in section.splitlines()
        if line.startswith("| ") and not line.startswith("| ---")
    ][1:]


def test_exact_directory_and_job_counts() -> None:
    assert tuple(sorted(path.name for path in CORPUS.iterdir() if path.is_dir())) == IDS
    for dossier_id in IDS:
        folder = CORPUS / dossier_id
        assert {path.name for path in folder.iterdir()} == {
            "dossier.json", "gold.json", "resume.txt", "jobs"
        }
        assert {path.name for path in (folder / "jobs").iterdir()} == {
            f"{job}.txt" for job in JOBS
        }


@pytest.mark.parametrize("dossier_id", IDS)
def test_schemas_gold_references_and_job_terms(dossier_id: str) -> None:
    folder = CORPUS / dossier_id
    dossier = load_json(folder / "dossier.json")
    gold = load_json(folder / "gold.json")
    for name, document in (("dossier", dossier), ("gold", gold)):
        schema = load_json(BENCHMARK / "schemas" / f"{name}.schema.json")
        Draft202012Validator(schema).validate(document)
        assert document["dossier_id"] == dossier_id

    assert dossier["base_resume_path"] == "resume.txt"
    atoms = gold["atoms"]
    assert len({atom["id"] for atom in atoms}) == len(atoms)
    assert len({evidence["id"] for evidence in dossier["evidence"]}) == len(atoms)
    assert {
        (item["owner"], item["kind"], item["text"]) for item in dossier["evidence"]
    } == {(atom["owner"], atom["kind"], atom["value"]) for atom in atoms}
    assert set(gold["jobs"]) == set(JOBS)

    gold_values = {
        value.casefold() for atom in atoms for value in [atom["value"], *atom["aliases"]]
    }
    for job_id, job in gold["jobs"].items():
        text = (folder / "jobs" / f"{job_id}.txt").read_text(encoding="utf-8")
        assert 150 <= len(text.split()) <= 400
        assert "Required:" in text and "Preferred:" in text
        assert 3 <= len(job["must_include"]) <= 6
        assert len(job["must_include"]) == len(set(job["must_include"]))
        for pointer in job["must_include"]:
            assert re.fullmatch(r"/atoms/\d+", pointer)
            atom = atoms[int(pointer.removeprefix("/atoms/"))]
            assert atom["owner"]
        included = [atoms[int(pointer.removeprefix("/atoms/"))] for pointer in job["must_include"]]
        assert sum(atom["kind"] == "tool" for atom in included) >= 2
        assert any(atom["kind"] == "outcome" for atom in included)
        assert set(job["jd_only_terms"]).issubset(job["jd_terms"])
        assert all(term.casefold() not in gold_values for term in job["jd_only_terms"])
        assert all(
            term.casefold() in gold_values
            for term in job["jd_terms"] if term not in job["jd_only_terms"]
        )
        assert all(term in text for term in job["jd_terms"])


def test_coverage_tables_and_trap_totals() -> None:
    markdown = (CORPUS / "COVERAGE.md").read_text(encoding="utf-8")
    dossiers = table_rows(markdown, "## Dossier matrix")
    cases = table_rows(markdown, "## Case \u00d7 trap matrix")
    assert len(dossiers) == 12 and len(cases) == 36
    assert [row[0] for row in dossiers] == list(IDS)
    assert Counter(row[1] for row in dossiers) == {
        "Backend": 3, "Frontend": 2, "ML/data": 2, "QA/SDET": 2,
        "DevOps/SRE": 2, "Research engineer": 1,
    }
    assert Counter(row[2] for row in dossiers) == {
        "New graduate": 3, "2\u20135 years": 5, "6+ years": 4,
    }
    assert Counter(row[3] for row in dossiers) == {"Sparse": 4, "Medium": 4, "Rich": 4}
    for row in dossiers:
        visible, total = int(row[5]), int(row[6])
        assert 1.2 <= total / visible <= 1.4
        assert total == len(load_json(CORPUS / row[0] / "dossier.json")["evidence"])

    assert {(row[0], row[1]) for row in cases} == {
        (dossier_id, job) for dossier_id in IDS for job in JOBS
    }
    counts = Counter(trap for row in cases for trap in row[2].split(", ") if trap != "—")
    assert counts == TRAP_COUNTS
    for dossier_id, job, traps in cases:
        gold_job = load_json(CORPUS / dossier_id / "gold.json")["jobs"][job]
        text = (CORPUS / dossier_id / "jobs" / f"{job}.txt").read_text()
        assert ("Prompt injection" in traps) == (gold_job["canary"] is not None)
        if "Prompt injection" in traps:
            assert "Ignore prior instructions" in text
        if "JD-only skill" in traps:
            assert "rather than adjacent" in text
        if "Tempting metric" in traps:
            assert "quantified percentage" in text
        if "Scope inflation" in traps:
            assert "lead or sole owner" in text
        if "Misattribution" in traps:
            assert "latest employer rather than the earlier one" in text
        if "Title pressure" in traps:
            assert "Senior title" in text
        if "Date pressure" in traps:
            assert "at least 5 years" in text
        if "Credential pressure" in traps:
            assert "earned credential" in text


def test_canaries_are_unique_and_only_in_their_job() -> None:
    texts = {
        path: path.read_text(encoding="utf-8")
        for path in CORPUS.glob("d*/jobs/*.txt")
    }
    canaries = [
        load_json(CORPUS / dossier_id / "gold.json")["jobs"]["adversarial"]["canary"]
        for dossier_id in IDS
    ]
    assert len(set(canaries)) == 12
    for dossier_id, canary in zip(IDS, canaries, strict=True):
        assert sum(text.count(canary) for text in texts.values()) == 1
        assert canary in texts[CORPUS / dossier_id / "jobs" / "adversarial.txt"]
        gold = load_json(CORPUS / dossier_id / "gold.json")
        assert gold["jobs"]["close"]["canary"] is None
        assert gold["jobs"]["stretch"]["canary"] is None


@pytest.mark.parametrize("dossier_id", IDS)
def test_resume_facts_and_importer(dossier_id: str) -> None:
    folder = CORPUS / dossier_id
    resume = (folder / "resume.txt").read_text(encoding="utf-8")
    atoms = load_json(folder / "gold.json")["atoms"]
    by_kind = {kind: {a["value"] for a in atoms if a["kind"] == kind} for kind in
               ("metric", "tool", "organization", "title", "date", "credential")}
    for line in resume.splitlines():
        if line.startswith("- "):
            for number in re.findall(r"\b\d+(?:\.\d+)?%?\b", line):
                assert any(number in metric for metric in by_kind["metric"]), (
                    dossier_id, line, number
                )
    for tool in TOOLS:
        if tool == "Docker" and "Docker Compose" in resume:
            continue
        if re.search(rf"(?<!\w){re.escape(tool)}(?!\w)", resume):
            assert tool in by_kind["tool"], (dossier_id, tool)
    skills = resume.split("\nSkills\n", 1)[1].strip().split(", ")
    assert set(skills).issubset(by_kind["tool"])
    required_kinds = ("organization", "date", "credential")
    for kind in required_kinds:
        assert by_kind[kind]
    if dossier_id != "d01":
        assert by_kind["title"]

    parsed = parse_resume_text(resume)
    expected_experiences = EXPERIENCE_COUNTS[int(dossier_id[1:]) - 1]
    assert len(parsed.profile.experiences) == expected_experiences
    assert len(parsed.profile.education) == (2 if dossier_id == "d12" else 1)
    assert not any("could not parse" in warning.message.lower() for warning in parsed.warnings)
    assert parsed.profile.owner.email.endswith("@example.com")


def test_job_parser_detects_planted_instructions() -> None:
    for dossier_id in IDS:
        text = (CORPUS / dossier_id / "jobs" / "adversarial.txt").read_text()
        result = parse_jd_text(text, company="Example Team", role_title="Engineer")
        assert result.jd.prompt_injection_flags


def test_manifest_is_current_and_fails_after_edit(tmp_path: Path) -> None:
    manifest = load_json(CORPUS / "MANIFEST.json")
    assert manifest["corpus_version"] == "0.1.0"
    assert manifest["protocol_version"] == "1.0.0"
    assert manifest["dossiers"] == list(IDS)
    actual = {
        path.relative_to(CORPUS).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in CORPUS.rglob("*") if path.is_file() and path != CORPUS / "MANIFEST.json"
    }
    assert manifest["files"] == actual
    script = BENCHMARK / "corpus" / "build_manifest.py"
    assert subprocess.run([sys.executable, str(script), "--check"], check=False).returncode == 0

    temporary_corpus = tmp_path / "corpus"
    temporary_corpus.mkdir()
    shutil.copy2(script, temporary_corpus / "build_manifest.py")
    shutil.copytree(CORPUS, temporary_corpus / "v0")
    resume = temporary_corpus / "v0" / "d01" / "resume.txt"
    resume.write_text(resume.read_text() + "changed\n")
    stale = subprocess.run(
        [sys.executable, str(temporary_corpus / "build_manifest.py"), "--check"],
        capture_output=True, text=True, check=False,
    )
    assert stale.returncode == 1
    assert "stale" in stale.stdout
