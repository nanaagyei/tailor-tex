"""Independent line-level atomic claim extraction."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from tailortex_bench.audit.lexicon import SCOPE_WORDS, SENIORITY_WORDS

METRIC = re.compile(
    r"(?<!\w)(?:[$£€]\s?\d[\d,.]*|\d[\d,.]*\s?(?:%|x|\u00d7|\+|"
    r"engineers|people|reports|services|users|requests(?:/day)?|years?|months?|"
    r"hours?|days?|microservices|tests|pipelines)|"
    r"\d+\s?(?:to|\u2013|-)\s?\d+\s?(?:years?|months?|engineers|services))",
    re.IGNORECASE,
)
NUMBER_WORDS = (
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
    "twenty",
)
HEADING = re.compile(r"^\s*([^|—\n]{2,80})\s*(?:\||—)\s*([^|—\n]{2,80})\s*$")
DATE = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+20\d\d"
    r"\s*(?:-|\u2013|—|to)\s*(?:Present|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|"
    r"Sep|Oct|Nov|Dec)[a-z]*\s+20\d\d)",
    re.IGNORECASE,
)
ISO_DATE = re.compile(
    r"\b20\d\d-\d\d\s*(?:-|\u2013|\u2014|to)\s*(?:Present|20\d\d-\d\d)\b", re.IGNORECASE
)
CREDENTIAL = re.compile(
    r"\b(?:B\.S\.|M\.S\.|Ph\.D\.|Bachelor(?:'s)?|Master(?:'s)?|"
    r"Doctorate|Certified|Certification)(?:\s+[^|\n,;]+)?",
    re.IGNORECASE,
)
ORGANIZATION = re.compile(
    r"\b[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\s+"
    r"(?:Systems|Works|Labs|Institute|College|Inc)\b"
)


def normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def contains_term(line: str, term: str) -> bool:
    return (
        re.search(r"(?<![\w.+#])" + re.escape(term) + r"(?![\w.+#])", line, re.IGNORECASE)
        is not None
    )


@dataclass(frozen=True)
class Extracted:
    kind: str
    value: str
    line: int
    owner: str | None


def _matches(line: str, terms: list[str]) -> list[str]:
    found: list[str] = []
    spans: list[tuple[int, int]] = []
    for term in sorted(set(terms), key=lambda term: (-len(term), term.casefold())):
        match = re.search(r"(?<![\w.+#])" + re.escape(term) + r"(?![\w.+#])", line, re.IGNORECASE)
        if match and not any(match.start() < end and match.end() > start for start, end in spans):
            found.append(line[match.start() : match.end()])
            spans.append(match.span())
    return found


def _project_names(resume: str) -> dict[str, str]:
    names: dict[str, str] = {}
    section = ""
    for line in resume.splitlines():
        value = line.strip()
        if value in {"Summary", "Experience", "Projects", "Education", "Skills"}:
            section = value
        elif section == "Projects" and value and not value.startswith("-"):
            names[normalize(value)] = f"project-{len(names) + 1}"
    return names


def extract_atoms(
    text: str,
    gold: dict[str, Any],
    job_gold: dict[str, Any],
    tool_terms: list[str],
    resume: str | None = None,
) -> tuple[list[Extracted], list[dict[str, Any]]]:
    atoms: list[Extracted] = []
    candidates: list[dict[str, Any]] = []
    owner: str | None = None
    gold_atoms = gold["atoms"]
    by_kind = {
        kind: [
            value
            for atom in gold_atoms
            if atom["kind"] == kind
            for value in [atom["value"], *atom["aliases"]]
        ]
        for kind in ("organization", "title", "date", "credential", "outcome")
    }
    terms = [*tool_terms, *job_gold["jd_terms"], *job_gold["jd_only_terms"]]
    project_names = _project_names(resume) if resume is not None else {}
    section = ""
    for line_no, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped in {"Summary", "Experience", "Projects", "Education", "Skills"}:
            section = stripped
            owner = {"Education": "education", "Skills": "candidate"}.get(section)
            continue
        if resume is not None and not section:
            continue
        if section == "Projects" and normalize(stripped) in project_names:
            owner = project_names[normalize(stripped)]
            continue
        heading = HEADING.match(stripped) if section == "Experience" or resume is None else None
        if heading:
            organization = heading.group(2).strip()
            title = heading.group(1).strip()
            matching = [
                atom
                for atom in gold_atoms
                if atom["kind"] == "organization"
                and any(
                    normalize(organization) == normalize(value)
                    for value in [atom["value"], *atom["aliases"]]
                )
            ]
            title_owners = {
                atom["owner"]
                for atom in gold_atoms
                if atom["kind"] == "title"
                and any(
                    normalize(title) == normalize(value)
                    for value in [atom["value"], *atom["aliases"]]
                )
            }
            owner = next(
                (atom["owner"] for atom in matching if atom["owner"] in title_owners),
                matching[0]["owner"] if matching else f"unknown:{normalize(organization)}",
            )
        else:
            orgs = _matches(line, by_kind["organization"])
            if stripped in orgs:
                match = next(
                    (
                        atom
                        for atom in gold_atoms
                        if atom["kind"] == "organization"
                        and normalize(stripped)
                        in [normalize(v) for v in [atom["value"], *atom["aliases"]]]
                    ),
                    None,
                )
                if match:
                    owner = match["owner"]
        for kind in ("organization", "title", "date", "credential", "outcome"):
            for value in _matches(line, by_kind[kind]):
                atoms.append(Extracted(kind, value, line_no, owner))
        if heading:
            for kind, value in (
                ("title", heading.group(1).strip()),
                ("organization", heading.group(2).strip()),
            ):
                if not any(
                    a.kind == kind and a.line == line_no and normalize(a.value) == normalize(value)
                    for a in atoms
                ):
                    atoms.append(Extracted(kind, value, line_no, owner))
        for match in (
            ORGANIZATION.finditer(line)
            if section in ("Experience", "Education") or resume is None
            else []
        ):
            value = match.group()
            if stripped != value:
                continue
            if not any(
                a.kind == "organization"
                and a.line == line_no
                and normalize(a.value) == normalize(value)
                for a in atoms
            ):
                atoms.append(Extracted("organization", value, line_no, owner))
        for match in DATE.finditer(line):
            value = match.group()
            if not any(
                a.kind == "date" and a.line == line_no and normalize(a.value) == normalize(value)
                for a in atoms
            ):
                atoms.append(Extracted("date", value, line_no, owner))
        for match in ISO_DATE.finditer(line):
            atoms.append(Extracted("date", match.group(), line_no, owner))
        for match in CREDENTIAL.finditer(line):
            value = match.group().strip()
            if not any(
                a.kind == "credential"
                and a.line == line_no
                and normalize(value).startswith(normalize(a.value))
                for a in atoms
            ):
                atoms.append(Extracted("credential", value, line_no, owner))
        for match in METRIC.finditer(line):
            atoms.append(Extracted("metric", match.group().strip(), line_no, owner))
        for number in NUMBER_WORDS:
            for match in re.finditer(
                rf"\b{number}\s+(?:engineers|people|reports|services|"
                r"years?|months?|pipelines)\b",
                line,
                re.IGNORECASE,
            ):
                atoms.append(Extracted("metric", match.group(), line_no, owner))
        for value in _matches(line, terms):
            atoms.append(Extracted("tool", value, line_no, owner))
        for word in SCOPE_WORDS:
            for match in re.finditer(rf"\b{word}\b", line, re.IGNORECASE):
                atoms.append(Extracted("scope", match.group(), line_no, owner))
        for match in re.finditer(r"\b(?:team of \d+|\d+ reports)\b", line, re.IGNORECASE):
            atoms.append(Extracted("scope", match.group(), line_no, owner))
        if heading:
            for word in SENIORITY_WORDS:
                if contains_term(heading.group(1), word):
                    atoms.append(Extracted("scope", word, line_no, owner))
        if not any(a.kind == "outcome" and a.line == line_no for a in atoms):
            for verb in ("eliminated", "accelerated", "increased", "created"):
                match = re.search(rf"\b{verb}\b[^.;\n]{{3,80}}", line, re.IGNORECASE)
                if match and stripped.startswith("-"):
                    atoms.append(Extracted("outcome", match.group().strip(), line_no, owner))
                    break
        known = {normalize(term) for term in terms}
        for token in re.findall(r"\b[A-Z][A-Za-z0-9.+#]*\b", line):
            if normalize(token) not in known and (
                any(ch in token for ch in ".+#") or (token.isupper() and len(token) > 1)
            ):
                candidates.append({"value": token, "line": line_no, "kind": "tool?"})
    unique = {(a.kind, normalize(a.value), a.line, a.owner): a for a in atoms}
    return sorted(unique.values(), key=lambda a: (a.line, a.kind, a.value)), candidates
