# Benchmark definition

This directory defines how synthetic resume-tailoring cases are evaluated. The
JSON files in examples/ illustrate file shapes; they are not measured outcomes.
No real candidate information belongs here.

Read in this order:

1. [PROTOCOL.md](PROTOCOL.md) defines cases, claim audits, formulas, and fairness rules.
2. [RUBRIC.md](RUBRIC.md) gives blind human raters a common scoring procedure.
3. [prompts/baseline-v1.md](prompts/baseline-v1.md) fixes the prompt-only baseline.
4. The [schema files](schemas/dossier.schema.json) define six versioned JSON
   formats; the [examples](examples/dossier.example.json) contain one synthetic
   document for each.

5. The [synthetic corpus](corpus/README.md) supplies fixed candidate and job
   inputs with owner-linked gold facts and planted traps.

## How to run

Install `packages/bench` with `uv sync`, then run `uv run tailortex-bench
validate-corpus`, `uv run tailortex-bench calibrate-auditor`, and `uv run
tailortex-bench run --system tailortex --repeat 2`. See the
[bench package guide](../packages/bench/README.md) for all adapters, outputs,
and reports.
Protocol version 1.0.0 is a measurement definition, not a performance claim.
