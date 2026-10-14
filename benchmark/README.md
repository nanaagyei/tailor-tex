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

The corpus and executable harness are separate follow-up issues (#11 and #12).
Protocol version 1.0.0 is a measurement definition, not a performance claim.
