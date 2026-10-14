# TailorTex

<p align="center"><img src="images/logo.png" alt="TailorTex logo" width="180" /></p>

**An open-source, local-first career-evidence compiler for technical resumes.**

TailorTex's goal is the [career-evidence compiler described in ADR-0001](docs/adr/0001-career-evidence-compiler.md): for technical job seekers who tailor many applications, produce reproducible, job-specific resumes without silently inventing claims, with every output line selected from or explicitly linked to approved evidence. The evidence guarantees in that goal are still being built; the table below distinguishes what works today from what is planned.

TailorTex is not a generic resume writer, an ATS oracle, a template marketplace, a job board, or a general document platform.

## Capability status

<!-- Update a row to Implemented only when its linked test covers the shipped behavior. -->

| Capability | Status | Evidence |
| --- | --- | --- |
| Import PDF, DOCX, Markdown, and text into a draft profile | Implemented | [Parser tests](packages/core/tests/test_parsers.py) |
| Local workspace with path-traversal protection | Implemented | [Workspace tests](packages/core/tests/test_workspace.py) |
| Job description parsing with prompt-injection flags | Implemented | [JD parser tests](packages/core/tests/test_jd_parser.py) |
| Deterministic LaTeX rendering with escaping | Implemented | [Rendering tests](packages/core/tests/test_rendering.py) |
| Detection of added metrics, listed tools, and leadership phrases | Implemented | [Validation tests](packages/core/tests/test_validation.py) |
| Only approved evidence reaches the output | Planned | [#15](https://github.com/nanaagyei/tailor-tex/issues/15), [#16](https://github.com/nanaagyei/tailor-tex/issues/16) |
| Every output line mapped to evidence | Planned | [#17](https://github.com/nanaagyei/tailor-tex/issues/17) |
| Build fails on unsupported claims | Planned | [#18](https://github.com/nanaagyei/tailor-tex/issues/18) |
| Model-assisted rewriting with consent and redaction | Planned | [#19](https://github.com/nanaagyei/tailor-tex/issues/19) |
| Reproducible builds | Planned | [#20](https://github.com/nanaagyei/tailor-tex/issues/20) |
| Public benchmark | Planned | [#10](https://github.com/nanaagyei/tailor-tex/issues/10), [#26](https://github.com/nanaagyei/tailor-tex/issues/26) |

The current CLI imports a draft, lets you review and approve its items together, parses a job description, and generates single-column LaTeX with no data tables or content images. The template uses layout tables to align headings. Approval is currently coarse (`--all`); output evidence enforcement and build failure on rejected claims are planned. The `validate` command is also [planned](https://github.com/nanaagyei/tailor-tex/issues/18).

## Quick start

Install Python 3.12+, [uv](https://docs.astral.sh/uv/), Node.js 20+, and [pnpm 10](https://pnpm.io/). From the repository root, run `make install`. The following shell block puts the CLI's virtual environment on your PATH, creates synthetic inputs in a temporary directory, and leaves that directory in place so you can inspect `out.tex`.

<!-- doctest:quickstart -->
```bash
export PATH="$PWD/apps/cli/.venv/bin:$PATH"
quickstart_dir="$(mktemp -d)"
cat > "$quickstart_dir/RESUME.txt" <<'EOF'
Jordan Example
Experience
QA Engineer | Example Systems
January 2022 - Present
- Automated Python tests for release checks.
Skills
Python
EOF
cat > "$quickstart_dir/JD.txt" <<'EOF'
QA Engineer. Required: Python experience.
EOF
tailortex init --workspace "$quickstart_dir/workspace"
tailortex import "$quickstart_dir/RESUME.txt" --workspace "$quickstart_dir/workspace"
tailortex profile review --workspace "$quickstart_dir/workspace"
tailortex profile approve --all --workspace "$quickstart_dir/workspace"
tailortex jd parse "$quickstart_dir/JD.txt" --workspace "$quickstart_dir/workspace" | tee "$quickstart_dir/jd-output.txt"
tailortex jd list --workspace "$quickstart_dir/workspace"
job_id="$(sed -n 's/^Saved: //p' "$quickstart_dir/jd-output.txt")"
tailortex tailor --jd "$job_id" --output "$quickstart_dir/out.tex" --workspace "$quickstart_dir/workspace"
```

The `Saved:` line from `jd parse` supplies the job ID used by `tailor`. Run `cat "$quickstart_dir/out.tex"` to inspect the generated LaTeX. These commands do not require an LLM provider.

## Current pipeline

```text
Resume file -> draft profile -> review and --all approval
                                   |
Job description -> parsed job ID -> deterministic selection and rewriting
                                   |
                         claim detection -> LaTeX rendering -> .tex

Future path (not in the current CLI):
  LLM Rewrite Layer (planned) -> evidence-linked output (planned)
  -> build failure on unsupported claims (planned)
```

The current claim detector reports findings, but tailoring may still export a `.tex` file when it reports rejected claims. Inspect the report and output before using either in an application.

## Privacy and security

Workspace data is stored locally, and TailorTex includes no telemetry, accounts, or hosted backend. Path traversal checks protect workspace file operations. Cloud-provider consent and redaction in the application call path are [planned in #19](https://github.com/nanaagyei/tailor-tex/issues/19); the current CLI uses deterministic rewriting. See [SECURITY.md](SECURITY.md) for the current security model and private vulnerability reporting.

## Documentation

- [CLI commands](apps/cli/README.md)
- [Core package](packages/core/README.md)
- [Documentation index](docs/README.md)
- [Benchmark protocol](benchmark/README.md)
- [Contributor guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

Distributed under the [MIT License](LICENSE).
