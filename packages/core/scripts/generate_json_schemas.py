#!/usr/bin/env python3
"""Generate JSON Schema files from Pydantic models.

Writes canonical-profile.schema.json and parsed-job-description.schema.json
to packages/core/schemas/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure the tailortex package is importable from its source root
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CORE_SRC = _REPO_ROOT / "packages" / "core" / "src"
_SCHEMAS_DIR = _REPO_ROOT / "packages" / "core" / "schemas"

sys.path.insert(0, str(_CORE_SRC))

from tailortex.schemas import CanonicalProfile, ParsedJobDescription  # noqa: E402


def _write_schema(model, filename: str) -> None:
    schema = model.model_json_schema()
    _SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = _SCHEMAS_DIR / filename
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
        f.write("\n")
    print(f"Wrote {output_path}")


def main() -> None:
    _write_schema(CanonicalProfile, "canonical-profile.schema.json")
    _write_schema(ParsedJobDescription, "parsed-job-description.schema.json")


if __name__ == "__main__":
    main()
