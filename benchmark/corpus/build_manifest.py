"""Build or verify the deterministic v0 corpus manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "v0"
MANIFEST = CORPUS / "MANIFEST.json"


def build_manifest(corpus: Path = CORPUS) -> dict[str, object]:
    dossiers = sorted(path.name for path in corpus.iterdir() if path.is_dir())
    files = {
        path.relative_to(corpus).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(corpus.rglob("*"))
        if path.is_file() and path != corpus / "MANIFEST.json"
    }
    return {
        "corpus_version": "0.1.0",
        "protocol_version": "1.0.0",
        "dossiers": dossiers,
        "files": files,
    }


def render_manifest(corpus: Path = CORPUS) -> str:
    return json.dumps(build_manifest(corpus), indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if MANIFEST.json is stale")
    args = parser.parse_args()
    expected = render_manifest()
    if args.check:
        if not MANIFEST.exists() or MANIFEST.read_text(encoding="utf-8") != expected:
            print("Corpus manifest is stale; run python benchmark/corpus/build_manifest.py")
            return 1
        print("Corpus manifest is current")
        return 0
    MANIFEST.write_text(expected, encoding="utf-8")
    print(f"Wrote {MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
