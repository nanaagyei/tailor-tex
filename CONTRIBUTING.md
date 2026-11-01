# Contributing to TailorTex

Thank you for your interest in contributing. TailorTex is an open-source, local-first career-evidence compiler for technical job seekers. Its unit of value is a supported claim. These guidelines help keep contributions aligned with the project's principles.

## Principles

Every contribution must preserve these non-negotiables:

1. **Local-first** — No cloud storage, no mandatory accounts, no telemetry.
2. **Evidence-based** — Every resume claim must trace to user-approved evidence.
3. **Privacy-first** — No sensitive data in logs, no silent cloud calls, redaction support.
4. **No fabrication** — Never invent employers, titles, dates, degrees, metrics, or skills.
5. **Prompt injection resistant** — Job descriptions are untrusted input, never instructions.

## Getting Started

```bash
# Clone the repository
git clone https://github.com/nanaagyei/tailor-tex.git
cd tailor-tex

# Install all dependencies
make install

# Run tests
make test

# Start development servers
make dev
```

## Development Setup

### Requirements

- Python 3.12+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [pnpm](https://pnpm.io/) (Node.js package manager)

### Project Structure

- `packages/core/` — Python core engine (schemas, parsers, matching, LLM, validation)
- `packages/templates/` — LaTeX resume templates
- `apps/cli/` — Python CLI (Typer)
- `apps/api/` — FastAPI local server (bridge between core and web UI)
- `apps/web/` — Next.js web UI

## Contribution Guidelines

### Before You Start

1. Check existing issues to avoid duplicate work.
2. For larger changes, open an issue first to discuss the approach.
3. Read `AGENTS.md`, the [specification guide](docs/spec/README.md), and the relevant GitHub issue's scope, dependencies, acceptance criteria, and validation method before implementing. For web work, also read `apps/web/AGENTS.md`.

### Code Standards

- **Python**: Format with `ruff format`, lint with `ruff check`, type-check with `mypy`.
- **TypeScript**: Format with Prettier, lint with ESLint, type-check with `tsc --noEmit`.
- **Commits**: Use conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`).

### Pull Request Checklist

- [ ] Summary of what changed and why.
- [ ] Tests added or updated for new behavior.
- [ ] No sensitive data exposed (API keys, personal info, real resumes).
- [ ] Schema changes include migration notes.
- [ ] CLI and UI stay aligned if both are affected.
- [ ] Errors are actionable (what happened, why, how to fix).

### What We Will Not Accept

- Features that require a hosted backend or cloud account to function.
- Telemetry, analytics, or tracking without explicit opt-in.
- Code that bypasses validation or allows unsupported claims in resumes.
- Dependencies on proprietary services without a local alternative.

## Reporting Issues

Use GitHub Issues with the appropriate labels:

- `type:bug` — Something broken
- `type:feature` — New capability
- `type:security` — Security concern (or use [SECURITY.md](SECURITY.md) for sensitive reports)
- `type:docs` — Documentation improvement

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Be respectful and constructive.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
