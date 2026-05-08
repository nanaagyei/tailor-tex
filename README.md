# TailorTex

**Local-first resume tailoring workbench.**

TailorTex helps technical job seekers convert their verified career profile and target job descriptions into truthful, ATS-readable LaTeX resumes — without sending data to the cloud.

## Why TailorTex?

Most resume tools either require cloud accounts (privacy risk), produce generic output (no real tailoring), or fabricate claims (keyword stuffing). TailorTex is different:

- **Local-first** — Your data never leaves your machine unless you explicitly choose a cloud LLM provider.
- **Evidence-based** — Every generated claim traces back to your approved source material. No fabrication.
- **ATS-readable** — Clean, single-column LaTeX output designed for applicant tracking systems.
- **Open-source** — MIT licensed. No paywalls, no dark patterns, no telemetry.
- **Bring your own LLM** — Works with OpenAI, Anthropic, Ollama, LM Studio, or no LLM at all.

## Architecture

```
Resume / Career Docs
        |
    Parser Layer
        |
  Canonical Profile  ←  You review and approve
        |
  Job Description Parser  ←  Treated as untrusted input
        |
  Matching & Ranking
        |
  LLM Rewrite Layer  ←  Evidence-constrained, no fabrication
        |
  Truth Validator  ←  Claims checked against your evidence
        |
  LaTeX Renderer
        |
  .tex / PDF / Overleaf ZIP / Reports
```

## Quick Start

### Requirements

- Python 3.12+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [pnpm](https://pnpm.io/) (Node.js package manager)

### Install

```bash
git clone https://github.com/nanaagyei/tailor-tex.git
cd tailor-tex
make install
```

### Development

```bash
# Start both API server and web UI
make dev

# Run all tests
make test

# Lint all code
make lint
```

### CLI

```bash
# Initialize workspace
tailortex init

# Import a resume
tailortex import resume.pdf

# Review parsed profile
tailortex profile review

# Approve profile
tailortex profile approve

# Parse a job description
tailortex jd parse job.md

# Tailor resume to job
tailortex tailor <jd-id>

# Export artifacts
tailortex export <application-id>
```

## Project Structure

```
tailor-tex/
├── packages/core/          Python core engine
│   └── src/tailortex/
│       ├── schemas/        Pydantic data models
│       ├── parsers/        Resume & JD parsing
│       ├── matching/       Evidence scoring
│       ├── llm/            LLM provider interface
│       ├── validation/     Claim validation
│       ├── rendering/      LaTeX rendering
│       ├── storage/        Local workspace manager
│       └── privacy/        Redaction & disclosure
├── packages/templates/     LaTeX resume templates
├── apps/cli/               Command-line interface
├── apps/api/               FastAPI local server
└── apps/web/               Next.js web UI
```

## Privacy

TailorTex is designed to be safer than hosted resume services:

- All data stored locally in `~/.tailortex/` by default.
- Cloud LLM calls require explicit user consent via a disclosure modal.
- Redaction mode replaces sensitive entities before cloud transmission.
- No telemetry, no analytics, no tracking.

See [SECURITY.md](SECURITY.md) for the full security model.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Key principles:

1. Preserve local-first behavior.
2. Never bypass validation or enable fabrication.
3. Include tests for new behavior.
4. Protect user privacy.

## License

[MIT](LICENSE)
