"""Benchmark format examples must stay valid and reject unknown fields."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

BENCHMARK = Path(__file__).resolve().parents[3] / "benchmark"
NAMES = (
    "dossier",
    "gold",
    "system-output",
    "claim-audit",
    "results",
    "human-rating",
)


def load_pair(name: str) -> tuple[dict, dict]:
    schema = json.loads((BENCHMARK / "schemas" / f"{name}.schema.json").read_text())
    example = json.loads((BENCHMARK / "examples" / f"{name}.example.json").read_text())
    return schema, example


@pytest.mark.parametrize("name", NAMES)
def test_example_validates_against_draft_2020_12_schema(name: str) -> None:
    schema, example = load_pair(name)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(example)


@pytest.mark.parametrize("name", NAMES)
def test_unknown_property_is_rejected(name: str) -> None:
    schema, example = load_pair(name)
    example["unexpected_property"] = "must fail"
    with pytest.raises(ValidationError, match="Additional properties"):
        Draft202012Validator(schema).validate(example)


@pytest.mark.parametrize("name", NAMES)
def test_every_object_shape_rejects_extra_fields(name: str) -> None:
    schema, _ = load_pair(name)

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node.get("additionalProperties") is False
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(schema)
