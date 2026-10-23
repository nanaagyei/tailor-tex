# TailorTex benchmark harness

`tailortex-bench` runs the fixed synthetic corpus under the rules in
[PROTOCOL.md](../../benchmark/PROTOCOL.md). It does not read real career data.
From this directory, run `uv sync` (Python 3.12+). The normal run directory,
`benchmark/runs/<system>/`, is ignored by Git.

## Commands

```bash
uv run tailortex-bench validate-corpus
uv run tailortex-bench calibrate-auditor
uv run tailortex-bench run --system untailored
uv run tailortex-bench run --system tailortex --repeat 2
uv run tailortex-bench run --system prompt-baseline --provider mock
uv run tailortex-bench run --system external --name sample --outputs-dir /path/to/manual-outputs
uv run tailortex-bench audit --outputs ../../benchmark/runs/tailortex
uv run tailortex-bench report --results ../../benchmark/runs/tailortex/results.json
```

`run` accepts `--corpus PATH`, `--out DIR`, `--cases d01:close,d02:stretch`,
and `--repeat N`. It writes one schema-validated `<dossier>__<job>.json` and
claim audit per scored case, `results.json`, and `results.run-manifest.json`.
The manifest records the command, calibration, uncertain tool candidates,
reproducibility measurement, product commit, and missing external cases. Missing
cases are excluded from scored denominators. `report` reads the manifest next
to each result and accepts repeated `--results` options to combine systems.
`--format json --out FILE` writes a combined schema-valid result and adjacent
manifest; `--format md` writes the metric and trap tables.

For external outputs, supply exactly one file named
`<dossier_id>__<job_id>.<txt|md|pdf|docx>` per case. The adapter only reads
these manually produced files. The prompt adapter uses the fixed
[baseline prompt](../../benchmark/prompts/baseline-v1.md). `mock` returns a
truthful canned base resume so CI makes no provider call. For `anthropic`,
`openai`, or `ollama`, provide `--model NAME`; cloud keys are read only from
`TAILORTEX_ANTHROPIC_API_KEY` or `TAILORTEX_OPENAI_API_KEY`. Install the optional
`providers` dependency group for HTTP calls. A cloud run announces the
synthetic-text disclosure before its first request.

Exit codes are 0 for success, 2 for corpus, schema, or calibration failure,
4 for provider configuration/request failure, and 1 for other errors. The
auditor does not import TailorTex matching or validation. Its calibration set
has 40 manually labelled examples; a score below 0.90 precision or recall is
a stop condition, never a threshold to lower.
