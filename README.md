# TailorTex

<p align="center">
  <img src="images/logo.png" alt="TailorTex logo" width="180" />
</p>

<p align="center"><strong>Local-first, evidence-based resume tailoring for serious job applications.</strong></p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-10b981.svg" alt="License: MIT" /></a>
  <img src="https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white" alt="Python 3.12+" />
  <img src="https://img.shields.io/badge/node-20%2B-339933?logo=node.js&logoColor=white" alt="Node 20+" />
  <img src="https://img.shields.io/badge/pnpm-9%2B-F69220?logo=pnpm&logoColor=white" alt="pnpm 9+" />
  <img src="https://img.shields.io/badge/PRs-welcome-0ea5e9.svg" alt="PRs welcome" />
</p>

TailorTex helps technical job seekers convert verified career evidence and target job descriptions into truthful, ATS-readable LaTeX resumes, without forcing cloud-first workflows.

## Key Features

- **Local-first by default**: keep data on your machine and work fully offline.
- **Evidence-constrained generation**: every claim is backed by approved source material.
- **Truth validation pipeline**: blocks unsupported or fabricated resume bullets.
- **ATS-friendly output**: clean, single-column LaTeX optimized for parsing.
- **Bring-your-own model**: use OpenAI, Anthropic, Ollama, LM Studio, or no LLM.
- **Open-source and auditable**: MIT licensed with transparent architecture.

## How It Works

```text
Resume / Career Docs
        |
    Parser Layer
        |
  Canonical Profile  <-  You review and approve
        |
  Job Description Parser  <-  Treated as untrusted input
        |
  Matching & Ranking
        |
  LLM Rewrite Layer  <-  Evidence-constrained
        |
  Truth Validator  <-  Claims checked against evidence
        |
  LaTeX Renderer
        |
  .tex / PDF / Overleaf ZIP / Reports
```

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/)
- [pnpm](https://pnpm.io/)

### Install

```bash
git clone https://github.com/nanaagyei/tailor-tex.git
cd tailor-tex
make install
```

### Run Locally

```bash
# Start API server and web app
make dev

# Run test suites
make test

# Run lint checks
make lint
```

## CLI Examples

```bash
# Initialize workspace
tailortex init

# Import and review profile evidence
tailortex import resume.pdf
tailortex profile review
tailortex profile approve

# Parse job and tailor resume
tailortex jd parse job.md
tailortex tailor <jd-id>

# Export deliverables
tailortex export <application-id>
```

## Repository Layout

```text
tailor-tex/
├── packages/core/          Python core engine
│   └── src/tailortex/
│       ├── schemas/        Pydantic models
│       ├── parsers/        Resume and JD parsing
│       ├── matching/       Evidence scoring and ranking
│       ├── llm/            Provider interfaces and guards
│       ├── validation/     Truth and consistency checks
│       ├── rendering/      LaTeX generation
│       ├── storage/        Local workspace management
│       └── privacy/        Redaction and disclosure controls
├── packages/templates/     LaTeX resume templates
├── apps/cli/               Command-line interface
├── apps/api/               FastAPI local server
└── apps/web/               Next.js web UI
```

## Privacy & Security

TailorTex is designed to reduce privacy risk compared to hosted resume builders:

- local storage under `~/.tailortex/` by default
- explicit disclosure before cloud model calls
- optional redaction mode for sensitive entities
- no telemetry, analytics, or tracking

For policy and threat model details, see [SECURITY.md](SECURITY.md).

## Documentation

- [Documentation index](docs/README.md) - project decisions and issue-tracker guidance
- [CONTRIBUTING.md](CONTRIBUTING.md) - contribution workflow and coding standards
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) - community expectations
- [SUPPORT.md](SUPPORT.md) - support channels and issue guidance
- [CHANGELOG.md](CHANGELOG.md) - release notes and notable changes

## Contributing

Contributions are welcome. Please open an issue for major changes first so we can align on scope and implementation approach.

Core project principles:

1. Preserve local-first behavior.
2. Never bypass validation or fabricate claims.
3. Add tests for behavior changes.
4. Keep privacy guarantees explicit and enforceable.

## License

Distributed under the [MIT License](LICENSE).
