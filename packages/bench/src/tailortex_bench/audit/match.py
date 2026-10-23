"""Gold-only verdicts; this module must stay independent of product validation."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from tailortex_bench.audit.extract import Extracted, extract_atoms, normalize


def _same(value: str, gold_value: str, kind: str) -> bool:
    left, right = normalize(value), normalize(gold_value)
    if left == right:
        return True
    if kind == "date":

        def parts(text: str) -> list[str]:
            found = re.findall(
                r"20\d\d-\d\d|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|"
                r"Oct|Nov|Dec)[a-z]*\s+20\d\d|Present",
                text,
                re.IGNORECASE,
            )
            converted = []
            for part in found:
                if re.fullmatch(r"20\d\d-\d\d", part):
                    converted.append(part)
                elif part.casefold() == "present":
                    converted.append("present")
                else:
                    converted.append(
                        datetime.strptime(part[:3] + part[-5:], "%b %Y").strftime("%Y-%m")
                    )
            return converted

        return parts(value) == parts(gold_value) and bool(parts(value))
    return kind in ("outcome", "scope") and (left in right or right in left)


def verdict(atom: Extracted, gold: dict[str, Any]) -> tuple[str, str | None]:
    matches = [
        (index, entry)
        for index, entry in enumerate(gold["atoms"])
        if entry["kind"] == atom.kind
        and any(
            _same(atom.value, value, atom.kind) for value in [entry["value"], *entry["aliases"]]
        )
    ]
    same_owner = [
        (index, entry)
        for index, entry in matches
        if atom.owner is None
        or entry["owner"] == atom.owner
        or (atom.kind == "tool" and entry["owner"] == "candidate" and atom.owner == "candidate")
    ]
    if same_owner:
        index, _ = same_owner[0]
        return "supported", f"/atoms/{index}"
    if matches:
        index, _ = matches[0]
        return "misattributed", f"/atoms/{index}"
    peers = [
        (index, entry)
        for index, entry in enumerate(gold["atoms"])
        if entry["kind"] == atom.kind and (atom.owner is None or entry["owner"] == atom.owner)
    ]
    if atom.kind == "metric":
        proposed = re.search(r"\d+(?:\.\d+)?", atom.value)
        if proposed:
            for index, entry in peers:
                known = re.search(r"\d+(?:\.\d+)?", entry["value"])
                if (
                    known
                    and float(proposed.group()) > float(known.group())
                    and (("%" in atom.value) == ("%" in entry["value"]))
                ):
                    return "inflated", f"/atoms/{index}"
    if atom.kind == "scope" and normalize(atom.value) in {
        "led",
        "managed",
        "directed",
        "headed",
        "owned",
        "oversaw",
        "spearheaded",
        "supervised",
        "principal",
        "staff",
        "senior",
    }:
        for index, entry in peers:
            if "contributed" in normalize(entry["value"]):
                return "inflated", f"/atoms/{index}"
    if atom.kind == "title":
        base = re.sub(r"^(senior|staff|principal)\s+", "", normalize(atom.value))
        for index, entry in peers:
            if base == normalize(entry["value"]):
                return "inflated", f"/atoms/{index}"
    return "unsupported", None


def audit_output(
    text: str,
    gold: dict[str, Any],
    job_gold: dict[str, Any],
    tool_terms: list[str],
    dossier_id: str,
    job_id: str,
    system_id: str,
    resume: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    extracted, candidates = extract_atoms(text, gold, job_gold, tool_terms, resume)
    audited = []
    for atom in extracted:
        result, reference = verdict(atom, gold)
        audited.append(
            {
                "kind": atom.kind,
                "value": atom.value,
                "line": atom.line,
                "verdict": result,
                "gold_ref": reference,
            }
        )
    return {
        "case": {"dossier_id": dossier_id, "job_id": job_id},
        "system_id": system_id,
        "atoms": audited,
    }, candidates
