# TailorTex benchmark results

- Corpus version: 0.1.0
- Protocol version: 1.0.0
- Auditor calibration: precision 1.000; recall 1.000
- Commands: `PYTHONPATH=/tmp/tailortex-main-baseline/packages/core/src .venv/bin/tailortex-bench run --system untailored --out /tmp/tt-baseline-untailored`; `PYTHONPATH=/tmp/tailortex-main-baseline/packages/core/src .venv/bin/tailortex-bench run --system tailortex --repeat 2 --out /tmp/tt-baseline-tailortex`; `PYTHONPATH=/tmp/tailortex-main-baseline/packages/core/src .venv/bin/tailortex-bench run --system prompt-baseline --provider mock --out /tmp/tt-baseline-prompt`
- Product commits: tailortex=a4d6304634cb388e9698cef6d69de5b617b4f50a

## Automated metrics

| System | unsupported_claim_count | unsupported_claim_rate | cases_with_unsupported | jd_only_insertions | supported_jd_coverage | material_omission_rate | tailoring_delta | injection_compliance | format_failures | reproducible |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| prompt-baseline | 0 | 0.000 | 0.000 | 0 | 1.000 | 0.361 | 0.000 | 0.000 | 0 | — |
| tailortex | 33 | 0.050 | 0.917 | 0 | 1.000 | 0.361 | 0.198 | 0.000 | 0 | 1.000 |
| untailored | 0 | 0.000 | 0.000 | 0 | 1.000 | 0.361 | 0.000 | 0.000 | 0 | — |

## Per-trap breakdown

| System | Trap | Cases | Unsupported cases | JD-only insertions | Injection compliance |
| --- | --- | ---: | ---: | ---: | ---: |
| prompt-baseline | Credential pressure | 4 | 0 | 0 | 0.000 |
| prompt-baseline | Date pressure | 3 | 0 | 0 | 0.000 |
| prompt-baseline | JD-only skill | 4 | 0 | 0 | 0.000 |
| prompt-baseline | Misattribution | 3 | 0 | 0 | 0.000 |
| prompt-baseline | Prompt injection | 12 | 0 | 0 | 0.000 |
| prompt-baseline | Scope inflation | 3 | 0 | 0 | 0.000 |
| prompt-baseline | Tempting metric | 4 | 0 | 0 | 0.000 |
| prompt-baseline | Title pressure | 3 | 0 | 0 | 0.000 |
| tailortex | Credential pressure | 4 | 4 | 0 | 0.000 |
| tailortex | Date pressure | 3 | 3 | 0 | 0.000 |
| tailortex | JD-only skill | 4 | 4 | 0 | 0.000 |
| tailortex | Misattribution | 3 | 3 | 0 | 0.000 |
| tailortex | Prompt injection | 12 | 11 | 0 | 0.000 |
| tailortex | Scope inflation | 3 | 2 | 0 | 0.000 |
| tailortex | Tempting metric | 4 | 3 | 0 | 0.000 |
| tailortex | Title pressure | 3 | 3 | 0 | 0.000 |
| untailored | Credential pressure | 4 | 0 | 0 | 0.000 |
| untailored | Date pressure | 3 | 0 | 0 | 0.000 |
| untailored | JD-only skill | 4 | 0 | 0 | 0.000 |
| untailored | Misattribution | 3 | 0 | 0 | 0.000 |
| untailored | Prompt injection | 12 | 0 | 0 | 0.000 |
| untailored | Scope inflation | 3 | 0 | 0 | 0.000 |
| untailored | Tempting metric | 4 | 0 | 0 | 0.000 |
| untailored | Title pressure | 3 | 0 | 0 | 0.000 |

## Notes

Missing external cases: none.

At this version `tailortex` returns approved bullet text unchanged and renders every profile entry, so its factuality figures reflect the absence of rewriting, not the presence of safeguards. See `tailoring_delta`.

The product source was `origin/main` at `a4d6304634cb388e9698cef6d69de5b617b4f50a` on 2026-10-22 (America/Chicago). To recreate the pinned checkout before the commands above, run `git worktree add --detach /tmp/tailortex-main-baseline a4d6304634cb388e9698cef6d69de5b617b4f50a`. The loaded `tailortex.__file__` resolved inside that checkout, and the adapter recorded the same commit. The benchmark's plain-text exporter serializes the pinned product's parsed and selected profile because this `main` commit has no Markdown exporter.

`prompt-baseline --provider mock` returns a fixed copy of the synthetic base resume. It exercises the versioned prompt and provider path without measuring model quality. The d12 three-line education entry still parses as two entries, including a spurious one; see `benchmark/corpus/KNOWN_IMPORT_GAPS.md`. The TailorTex unsupported claims in this run are primarily altered or incomplete rendered credentials from the current parser, not invented rewritten bullets. The calibration score applies to the labelled set and is not an estimate of performance on arbitrary resumes.
