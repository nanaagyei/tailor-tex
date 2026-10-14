#!/usr/bin/env python3
"""Check that relative Markdown links resolve to tracked files in this repository."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
INLINE_CODE_RE = re.compile(r"(`+).*?\1")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))")
REFERENCE_DEFINITION_RE = re.compile(
    r"^\s{0,3}\[(?!\^)[^\]]+\]:\s*(?:<([^>]+)>|(\S+))"
)


def extract_links(markdown: str) -> list[tuple[int, str]]:
    """Return inline Markdown link destinations and their source line numbers."""
    links: list[tuple[int, str]] = []
    fence: str | None = None

    for line_number, line in enumerate(markdown.splitlines(), start=1):
        fence_match = FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            if fence is None:
                fence = marker[:3]
            elif marker.startswith(fence):
                fence = None
            continue
        if fence is not None:
            continue

        without_code = INLINE_CODE_RE.sub("", line)
        for match in LINK_RE.finditer(without_code):
            destination = match.group(1) or match.group(2)
            if destination:
                links.append((line_number, destination))

        reference_match = REFERENCE_DEFINITION_RE.match(without_code)
        if reference_match:
            destination = reference_match.group(1) or reference_match.group(2)
            if destination:
                links.append((line_number, destination))

    return links


def _tracked_target(
    root: Path, source: PurePosixPath, destination: str
) -> PurePosixPath | None:
    """Resolve a local destination to a repository-relative tracked path."""
    parsed = urlsplit(destination)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None

    decoded_path = unquote(parsed.path)
    candidate = (
        root / decoded_path.lstrip("/")
        if decoded_path.startswith("/")
        else root / Path(source.as_posix()).parent / decoded_path
    ).resolve()
    try:
        relative = candidate.relative_to(root.resolve())
    except ValueError:
        return PurePosixPath("..").joinpath(PurePosixPath(decoded_path))
    return PurePosixPath(relative.as_posix())


def check_markdown_links(
    root: Path,
    markdown_files: set[PurePosixPath],
    tracked_files: set[PurePosixPath],
) -> list[str]:
    """Return diagnostics for relative Markdown links without tracked targets."""
    errors: list[str] = []
    for source in sorted(markdown_files, key=lambda path: path.as_posix()):
        source_path = root / source.as_posix()
        text = source_path.read_text(encoding="utf-8")
        for line_number, destination in extract_links(text):
            target = _tracked_target(root, source, destination)
            if target is not None and target not in tracked_files:
                errors.append(
                    f"{source.as_posix()}:{line_number}: broken relative link "
                    f"{destination!r} (expected tracked file {target.as_posix()})"
                )
    return errors


def tracked_repository_files(root: Path) -> set[PurePosixPath]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        PurePosixPath(path.decode("utf-8"))
        for path in result.stdout.split(b"\0")
        if path
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        tracked = tracked_repository_files(root)
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"Could not list tracked repository files: {error}", file=sys.stderr)
        return 2

    markdown_files = {path for path in tracked if path.suffix.lower() == ".md"}
    errors = check_markdown_links(root, markdown_files, tracked)
    if errors:
        print("Broken relative Markdown links:", file=sys.stderr)
        print("\n".join(errors), file=sys.stderr)
        return 1

    print(f"Checked relative Markdown links in {len(markdown_files)} tracked files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
