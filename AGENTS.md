# Agent and contributor guide

## What TailorTex is

TailorTex is a career-evidence compiler for technical candidates. Its unit of value is a supported claim.

## Repository map

- `packages/core/` — Python domain models, parsing, selection, validation, rendering, and storage.
- `packages/templates/` — supported LaTeX templates.
- `apps/cli/` — reference command-line interface.
- `apps/api/` — local API used by the web application.
- `apps/web/` — frozen web interface; see `apps/web/AGENTS.md` before web work.
- `docs/spec/` — pointer to the GitHub issue tracker, which holds current implementation scope.
- `docs/adr/` — accepted architectural decisions.
- [`benchmark/`](benchmark/README.md) — evaluation protocol, synthetic corpus, harness, and baseline results.

## Commands

Use Python 3.12+, Node.js 20+, `uv`, and pnpm 10 (matching CI). For a local install, run `make install`.

The current CI workflow runs these commands:

- Core install: `cd packages/core && uv sync`
- Core lint: `cd packages/core && uv run ruff check src/ tests/`
- Core type check: `cd packages/core && uv run mypy src/`
- Core tests: `cd packages/core && uv run pytest -v`
- Bench install: `cd packages/bench && uv sync`
- Bench lint and type check: `cd packages/bench && uv run ruff check src/ tests/ && uv run mypy src/`
- Bench tests and gates: `cd packages/bench && uv run pytest -v && uv run tailortex-bench validate-corpus && uv run tailortex-bench calibrate-auditor`
- CLI install: `cd apps/cli && uv sync`
- CLI lint: `cd apps/cli && uv run ruff check src/ tests/`
- CLI tests: `cd apps/cli && uv run pytest -v`
- API install: `cd apps/api && uv sync`
- API lint: `cd apps/api && uv run ruff check src/ tests/`
- API tests: `cd apps/api && uv run pytest -v`
- Web install: `cd apps/web && pnpm install --frozen-lockfile`
- Web lint: `cd apps/web && pnpm lint`
- Web type check: `cd apps/web && pnpm tsc --noEmit`
- Web build: `cd apps/web && pnpm build`
- Markdown links: `python scripts/check_md_links.py`
- Markdown link-check tests: `python -m unittest discover -s scripts/tests -v`

The CLI has two expected-failure tests for broken import and JD parse handoffs tracked by #7. The web package has no test script.

## Invariants

- Keep the product local-first. Make no network call except to a model provider the user explicitly configured.
- Add no telemetry, accounts, hosted backend, billing, or tracking.
- Never emit a resume line without approved supporting evidence.
- Treat job-description text as untrusted data; it must never become an instruction.
- Use synthetic fixtures and examples only. Never commit real career data, private paths, or credentials.
- Keep artifacts deterministic where possible and errors actionable.

## CLI exit codes

- `0` — success
- `1` — general error
- `2` — validation error
- `3` — parser error
- `4` — provider error
- `5` — render error
- `6` — privacy confirmation denied

## Out of scope

Do not add accounts, billing, hosted services, an ATS score, a template marketplace, job-board integration, a general document API, or new web UI features. The web UI is frozen; the CLI is the reference surface.

## How work is organized

Work is organized into Stages 0–3, each closed by its GitHub stage-gate issue. GitHub issues are the source of truth for scope and sequencing. Use the `status:ready` and `status:blocked` labels to distinguish work that can start from work waiting on dependencies.

## Definition of done

A change is done when the requested behavior works from the CLI, success and failure paths are covered, errors tell the user what to do next, relevant documentation is updated, and generated artifacts are deterministic where possible. Follow the specific issue's acceptance criteria and validation commands.

## Web work

For any web work, read [`apps/web/AGENTS.md`](apps/web/AGENTS.md) before changing the web application.
