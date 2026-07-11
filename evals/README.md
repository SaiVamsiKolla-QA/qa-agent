# Evals

Threshold-gated evaluation scaffold (DeepEval), separate from `tests/golden/`
on purpose: the golden suite is an honest harness whose results get
documented, while `evals/` is a **gate** — once thresholds are calibrated,
a score drop fails the build.

## Layout

- `golden_set.schema.json` — JSON Schema every eval case must satisfy.
  Field names match `tests/golden/golden_set.json`, plus a required
  per-case `thresholds` object.
- `golden/` — eval cases (one JSON file per case). `example_case.json`
  mirrors golden q01 with a deliberately modest threshold.
- `metrics.py` — deterministic DeepEval metrics (no LLM judge — this repo
  is local-only, so cloud-judged metrics are off the table).
- `test_gate.py` — the `eval_gate` pytest suite: schema validation always
  runs; live pipeline scoring skips when mimik is down.

## Run

```bash
poetry install --with evals
poetry run pytest evals/ -m eval_gate     # schema layer + live layer if mimik is up
```

## Adding a case

Copy `golden/example_case.json`, change `id`/fields, set thresholds the
current model can honestly meet (smollm2-360m baseline is 3/10 on the
golden set — calibrate per case, don't aspire). Schema validation will
catch shape mistakes before anything runs.
