# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in TailorTex, please report it responsibly.

**Do not open a public issue for security vulnerabilities.**

Instead, use [GitHub Security Advisories](https://github.com/nanaagyei/tailor-tex/security/advisories/new) to report vulnerabilities privately.

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Impact assessment
- Suggested fix (if you have one)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix or mitigation**: Depends on severity, but we aim for 30 days for critical issues

## Security Principles

TailorTex handles sensitive career data. Our security model:

1. **Local-first storage** — All data stays on the user's machine by default.
2. **No silent cloud calls** — Cloud LLM providers require explicit user consent via a disclosure modal.
3. **Redaction support** — Sensitive entities (names, companies, emails) can be redacted before cloud transmission.
4. **No logging of sensitive data** — Raw resumes, personal info, and API keys are excluded from logs.
5. **Path traversal prevention** — Workspace file operations validate all paths stay within the workspace directory.
6. **Prompt injection resistance** — Job descriptions are treated as untrusted data, never as LLM instructions.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.x     | Yes       |

## Secrets Management

- API keys: stored via environment variables or OS keychain, never committed to source.
- `.env` files are gitignored.
- The `.env.example` file contains only placeholder values.
