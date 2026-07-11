# CI reference

## Workflow inventory

One workflow, `.github/workflows/ci.yml`, two jobs:

| Job   | Trigger                          | Stages in order                                        |
| ----- | -------------------------------- | ------------------------------------------------------ |
| test  | PR + push to main                | `ruff check` → `ruff format --check` → `pytest` (unit + integration) |
| evals | cron 05:00 UTC + manual dispatch | `pytest evals/ -m eval_gate` (CPU, schema layer today)  |

## Reproduce CI locally (run before every push)

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest                         # unit + integration (no mimik needed)
poetry install --with evals               # once, for the eval group
poetry run pytest evals/ -m eval_gate -v  # schema layer + live layer if mimik is up
```

## Debugging failures

- **Where output lands:** pytest output is in the job log; the eval gate
  logs `eval_metric metric=... score=...` lines per case. No artifacts yet.
- **Re-running one stage:** run the matching command above; a single eval
  case re-runs with `poetry run pytest evals/ -k q01`.
- **Known gotcha — two eval layers:** schema validation always runs; the
  live layer needs mimik and *skips* when it is unreachable (skipped ≠
  passed — check the skip count in the summary). On CI the live layer
  always skips until a CI-hostable local runtime replaces mimik.
- **Known gotcha — integration tests download models:** `tests/integration/`
  pulls `all-MiniLM-L6-v2` (~90 MB) on first run; slow first CI run is
  normal, cached after.

## Conventions

- `evals/` gates, `tests/golden/` documents — do not blur them. Golden
  results are published honestly (RESULTS.md); eval thresholds fail builds.
- Thresholds are per-case in each JSON file, calibrated to what the current
  model honestly achieves — never aspirational.
- Metrics stay deterministic and judge-free: this repo is local-only, so
  no cloud LLM-as-judge, ever (see CLAUDE.md Forbidden Tools).
- New pytest markers must be registered in `pyproject.toml`.

## Do not touch

- Workflow trigger definitions (`on:` block and job-level `if:` guards).
- The `require_mimik` skip convention — live evals skip, never fail, when
  the runtime is down.
- The `evals` Poetry group stays optional so `poetry install` in the dev
  loop stays lean.
