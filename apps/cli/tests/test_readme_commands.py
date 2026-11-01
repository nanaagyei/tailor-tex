"""Keep the public README quick start in sync with the registered CLI."""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest
from click import Group
from typer.main import get_command
from typer.testing import CliRunner

from tailortex_cli.main import app


README = Path(__file__).resolve().parents[3] / "README.md"
MARKER = "<!-- doctest:quickstart -->"
RUNNER = CliRunner()


def quickstart_block(readme: str) -> str:
    match = re.search(rf"{re.escape(MARKER)}\s*```bash\n(.*?)\n```", readme, re.DOTALL)
    assert match is not None, "README quick start marker or bash block is missing"
    return match.group(1)


def command_lines(block: str) -> list[str]:
    return [line for line in block.splitlines() if line.startswith("tailortex ")]


def run_quickstart(readme: str, tmp_path: Path) -> None:
    block = quickstart_block(readme)
    inputs = re.findall(r"cat > \"\$quickstart_dir/([^\"]+)\" <<'EOF'\n(.*?)\nEOF", block, re.DOTALL)
    assert {name for name, _ in inputs} == {"RESUME.txt", "JD.txt"}
    for name, content in inputs:
        (tmp_path / name).write_text(content + "\n", encoding="utf-8")

    lines = command_lines(block)
    assert len(lines) == 7, "README must contain the seven commands from issue #7"
    job_id: str | None = None
    for line in lines:
        # The tee command preserves jd parse output for the shell's job_id assignment.
        cli_line = line.split(" | tee ", maxsplit=1)[0]
        args = shlex.split(cli_line)[1:]
        args = [
            arg.replace("$quickstart_dir", str(tmp_path)).replace("$job_id", job_id or "")
            for arg in args
        ]
        assert "$" not in " ".join(args), f"Unresolved shell variable in {line}"
        result = RUNNER.invoke(app, args)
        assert result.exit_code == 0, f"{line}\n{result.output}"
        if args[:2] == ["jd", "parse"]:
            saved = re.search(r"Saved:\s+(\S+)", result.output)
            assert saved is not None, result.output
            job_id = saved.group(1)

    assert job_id is not None
    assert (tmp_path / "out.tex").exists()


def test_readme_quickstart_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_quickstart(README.read_text(encoding="utf-8"), tmp_path)


def test_readme_quickstart_rejects_invalid_command(tmp_path: Path) -> None:
    readme = README.read_text(encoding="utf-8")
    altered = readme.replace("tailortex jd list --workspace", "tailortex jd invalid --workspace", 1)
    assert altered != readme
    with pytest.raises(AssertionError, match="tailortex jd invalid"):
        run_quickstart(altered, tmp_path)


def test_readme_commands_are_registered() -> None:
    readme = README.read_text(encoding="utf-8")
    root = get_command(app)
    assert isinstance(root, Group)
    mentions = re.findall(r"\btailortex\s+([a-z][\w-]*)(?:\s+([a-z][\w-]*))?", readme)
    assert mentions
    for first, second in mentions:
        command = root.get_command(None, first)
        assert command is not None, f"Unregistered README command: tailortex {first}"
        if isinstance(command, Group) and second:
            assert command.get_command(None, second) is not None, (
                f"Unregistered README command: tailortex {first} {second}"
            )


def test_every_command_help_runs() -> None:
    root = get_command(app)
    assert isinstance(root, Group)

    def check(group: Group, prefix: list[str]) -> None:
        for name in group.list_commands(None):
            command = group.get_command(None, name)
            assert command is not None
            path = [*prefix, name]
            result = RUNNER.invoke(app, [*path, "--help"])
            assert result.exit_code == 0, f"{' '.join(path)} --help\n{result.output}"
            if isinstance(command, Group):
                check(command, path)

    assert RUNNER.invoke(app, ["--help"]).exit_code == 0
    check(root, [])
