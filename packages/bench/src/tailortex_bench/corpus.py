"""Corpus loading and integrity checks."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CORPUS = ROOT / "benchmark/corpus/v0"
SCHEMAS = ROOT / "benchmark/schemas"


class CorpusError(ValueError):
    """Invalid or incomplete benchmark corpus."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CorpusError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CorpusError(f"Expected an object in {path}")
    return value


def validate_document(name: str, document: dict[str, Any]) -> None:
    schema = load_json(SCHEMAS / f"{name}.schema.json")
    errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda e: str(e.path))
    if errors:
        raise CorpusError(f"Invalid {name}: {errors[0].message}")


@dataclass(frozen=True)
class Case:
    dossier_id: str
    job_id: str
    resume: str
    job: str
    dossier: dict[str, Any]
    gold: dict[str, Any]
    corpus: Path

    @property
    def key(self) -> str:
        return f"{self.dossier_id}__{self.job_id}"


def load_corpus(path: Path = DEFAULT_CORPUS) -> tuple[dict[str, Any], list[Case]]:
    path = path.resolve()
    manifest = load_json(path / "MANIFEST.json")
    if manifest.get("protocol_version") != "1.0.0":
        raise CorpusError("Corpus protocol version must be 1.0.0")
    actual = {
        file.relative_to(path).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
        for file in path.rglob("*")
        if file.is_file() and file.name != "MANIFEST.json"
    }
    if actual != manifest.get("files"):
        raise CorpusError("Corpus manifest is stale; run python benchmark/corpus/build_manifest.py")
    cases: list[Case] = []
    for dossier_id in manifest.get("dossiers", []):
        folder = path / dossier_id
        dossier = load_json(folder / "dossier.json")
        gold = load_json(folder / "gold.json")
        validate_document("dossier", dossier)
        validate_document("gold", gold)
        if dossier.get("dossier_id") != dossier_id or gold.get("dossier_id") != dossier_id:
            raise CorpusError(f"Dossier ID mismatch for {dossier_id}")
        resume_path = folder / dossier["base_resume_path"]
        if not resume_path.is_file() or resume_path.resolve().parent != folder:
            raise CorpusError(f"Invalid resume path for {dossier_id}")
        resume = resume_path.read_text(encoding="utf-8")
        for job_id, job_gold in sorted(gold["jobs"].items()):
            job_path = folder / "jobs" / f"{job_id}.txt"
            if not job_path.is_file():
                raise CorpusError(f"Missing job {dossier_id}:{job_id}")
            for pointer in job_gold["must_include"]:
                try:
                    index = int(pointer.removeprefix("/atoms/"))
                    if pointer != f"/atoms/{index}":
                        raise ValueError(pointer)
                    gold["atoms"][index]
                except (ValueError, IndexError) as exc:
                    raise CorpusError(f"Invalid gold pointer {pointer} for {dossier_id}") from exc
            cases.append(
                Case(
                    dossier_id,
                    job_id,
                    resume,
                    job_path.read_text(encoding="utf-8"),
                    dossier,
                    gold,
                    path,
                )
            )
    return manifest, sorted(cases, key=lambda case: (case.dossier_id, case.job_id))
