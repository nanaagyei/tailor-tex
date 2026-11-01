# ADR-0001: Career-evidence compiler

## Status

Accepted.

## Context

Structured resume sources, deterministic rendering, and job-specific variants are available in other tools. TailorTex's distinct value is evidence integrity: users should be able to see what supports each claim and the build should fail safely when evidence does not support it.

## Decision

TailorTex is a career-evidence compiler for technical candidates. Its unit of value is a supported claim. It is free, open source, and local-first.

**Positioning:** "For technical job seekers who tailor many applications, TailorTex is the career-evidence compiler that produces reproducible, job-specific resumes without silently inventing claims, because every output line is selected from or explicitly linked to an approved source of truth."

TailorTex is known for failing safely when the evidence does not support a claim. It is not a generic resume writer, an ATS oracle, a template marketplace, a job board, or a general document platform.

## Consequences

- The CLI is the reference surface; the web UI is frozen.
- The project maintains one supported template.
- A public benchmark measures the project's evidence-integrity results.
- Reviewer workflows use files and do not require accounts or a hosted service.
- GitHub issues define implementation scope and sequencing.
