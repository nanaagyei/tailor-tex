# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Versioned benchmark protocol, human rating rubric, and validated JSON formats (#10).
- Repository checks now cover core, CLI, API, and web without masking failures (#9).
- Reviewable CLI resume drafts, approved profile handoff, and saved jobs shared by the CLI and API, with read support for legacy job records (#7).
- CLI and API test suites with CI jobs for both packages.
- Tracked contributor guidance, the career-evidence compiler decision, and a Markdown link check in CI.
- Initial monorepo structure with Python core, CLI, API, and Next.js web UI.
- Pydantic schemas for canonical profile, job description, resume plan, and validation report.
- Local workspace manager with path traversal prevention.
- shadcn/ui design system with Geist fonts, zinc palette, emerald accent.
- Project governance files (LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY).
