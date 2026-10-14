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

TailorTex handles sensitive career data. Current protections and planned controls are listed separately.

### In effect today

- **Local storage** — The CLI stores workspace data on the user's machine. Imported resume source text is stored in the local draft until approval or deletion.
- **Path traversal prevention** — Workspace file operations check that paths stay within the workspace directory.
- **Job-description injection flagging** — The parser flags suspicious instructions in job descriptions. The current CLI does not send them to a model provider.
- **No telemetry** — The application has no telemetry or tracking integration.

### Planned

- **Cloud-provider consent** — [#19](https://github.com/nanaagyei/tailor-tex/issues/19) will wire explicit consent into the application call path before provider requests.
- **Redaction in the call path** — [#19](https://github.com/nanaagyei/tailor-tex/issues/19) will wire redaction into provider requests. A redaction helper exists, but the CLI does not use it.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.x     | Yes       |

## Secrets Management

- Provider API-key configuration is planned in [#19](https://github.com/nanaagyei/tailor-tex/issues/19); the current CLI does not read the variables in `.env.example`.
- `.env` files are gitignored.
- The `.env.example` file contains only placeholder values.
