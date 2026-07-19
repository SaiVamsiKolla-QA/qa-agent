# ROADMAP — DeepEval Evaluation Framework

Master roadmap for evolving qa-expert-agent from a Phase-1 RAG system into a
continuously evaluated, provider-agnostic AI system. Derived from the DeepEval
audit (2026-07-19). This is a living document: update it at the end of every
phase.

Companion documents: [ARCHITECTURE.md](ARCHITECTURE.md) (how everything works),
[DECISIONS.md](DECISIONS.md) (why we chose what we chose),
[LEARNING_GUIDE.md](LEARNING_GUIDE.md) (concept handbook).

---

## Project Vision

A QA Expert Agent whose quality is *measured*, not assumed. Every commit runs
the agent against a golden dataset of ISTQB questions, scores the answers with
DeepEval metrics, and fails CI when quality drops below configurable
thresholds. The same dataset benchmarks any model — GPT, Claude, Gemini, Qwen,
Llama, Ollama, vLLM, local HuggingFace — behind one abstraction, so model
choice becomes an evidence-based decision instead of a guess.

## End Goal

1. **Golden dataset evaluation** — per-commit, threshold-gated, in CI.
2. **Model comparison** — one dataset, many models, a reproducible leaderboard
   (accuracy, latency, cost, hallucination, composite score).
3. **Deployment flexibility** — evaluation layer depends on zero specific
   providers; local-first runtime stays intact.

## Current Repository Status

Phase 1 of the *original* project (RAG agent) is complete: ingest → chunk →
embed → ChromaDB → CLI Q&A with abstain logic and citations. 52 tests, ruff
clean, honest 3/10 golden baseline published in RESULTS.md (bounded by the
tiny `smollm2-360m` runtime model).

What the audit found blocking for evaluation:

- `answer()` returned only a string — no traces for metrics (**fixed in
  eval Phase 1**).
- One hardcoded LLM client — no model injection (**fixed in eval Phase 1**).
- No `temperature`/`seed`/`max_tokens` control — non-deterministic runs
  (**fixed in eval Phase 1**).
- Keyword-substring scoring only; no reference answers; no run history; no CI
  at all; corpus not reproducible in CI (copyrighted PDFs are gitignored).

## Why DeepEval

The existing golden harness (`tests/golden/scoring.py`) matches keywords. It
caught real failures, but RESULTS.md itself documents what it cannot see:
semantic drift, citation accuracy, answer coherence. DeepEval provides
LLM-as-judge metrics (Answer Relevancy, Faithfulness, Hallucination,
G-Eval) plus a pytest-native harness, thresholds, and reporting — the
industry-standard step up from string matching, without an orchestration
framework (the repo's no-framework rule applies to *agent* frameworks, not
evaluation harnesses — see DECISIONS.md ADR-001).

## Architecture Evolution (summary)

```
Today:      question → qa_expert → ChromaDB → local LLM → string answer
Phase 1:    same flow, but answer() returns AgentResult (full trace) and the
            LLM client accepts injected models + deterministic settings
Phases 2-4: evaluation/ package — dataset v2, runners, DeepEval metrics
Phase 5:    GitHub Actions gate on every PR (frozen-context mode)
Phases 6-7: model adapters + benchmark leaderboard + trend dashboard
```

Full diagrams and component contracts: [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Phases

### Phase 1 — Repository preparation  ⟵ CURRENT PHASE (complete — awaiting review)
- **Goal:** make the agent evaluable without changing its behavior.
- **Deliverables:** documentation suite (this file, ARCHITECTURE.md,
  DECISIONS.md, LEARNING_GUIDE.md); `AgentResult` returned by
  `qa_expert.answer()`; client/model injection + `temperature`/`seed`/
  `max_tokens` in `llm_client.chat()`; `.env.example` updated; all existing
  tests passing.
- **Dependencies:** none.
- **Risks:** return-type change ripples into golden harness and CLI tests —
  mitigated by updating every caller in the same commit.
- **Success criteria:** `poetry run pytest` fully green; `qa-agent ask` output
  byte-identical to before; `answer()` exposes traces.
- **Estimated effort:** 3–4 focused hours (+ documentation).

### Phase 2 — Evaluation harness skeleton
- **Goal:** one golden case scored end-to-end through DeepEval.
- **Deliverables:** `deepeval` dependency (new `[eval]` group); `evaluation/`
  scaffold; dataset schema validator; `agent_runner` + `eval_runner` running
  one case with one metric; per-run artifacts in `evaluation/outputs/`.
- **Dependencies:** Phase 1. CLAUDE.md amendment allowing cloud judge models
  for the evaluation layer happens here.
- **Risks:** DeepEval / Python 3.13 version pin friction — verify at install.
- **Success criteria:** one command produces a scored JSON for case q01.
- **Estimated effort:** 4–6 h.

### Phase 3 — Golden dataset v2
- **Goal:** 30+ reviewed cases with reference answers and frozen contexts.
- **Deliverables:** `golden_v2.jsonl` (migrated 10 legacy cases + new ones);
  `expected_answer` / `ground_truth_facts` authored per case; frozen-context
  capture script; dataset README + review checklist.
- **Dependencies:** Phase 2.
- **Risks:** frozen excerpts vs ISTQB copyright (keep excerpts minimal);
  reference answers encode the quality bar — review like code.
- **Success criteria:** schema-valid dataset; frozen-context replay works
  without ChromaDB.
- **Estimated effort:** 6–10 h (mostly domain authoring).

### Phase 4 — Full metric suite
- **Goal:** all planned metrics running with configurable thresholds.
- **Deliverables:** metric registry driven by `configs/eval.yaml`;
  deterministic Abstain-Correctness and Citation-Validity metrics; G-Eval
  metrics (ISTQB terminology, five-part format); judge-model config;
  `summary.md`/`report.json` emitters; committed baseline + regression
  comparator.
- **Dependencies:** Phase 3.
- **Risks:** judge variance and cost — pin judge version, cache verdicts,
  spot-check against human judgment before trusting thresholds.
- **Success criteria:** full run emits all metrics; exit code respects
  thresholds.
- **Estimated effort:** 5–7 h.

### Phase 5 — CI integration
- **Goal:** every PR gated on evaluation quality.
- **Deliverables:** `.github/workflows/eval.yml` (lint/unit → smoke eval on
  PR; full eval nightly); dependency + HF caches; secrets wiring; sticky PR
  comment with summary; artifact upload; baseline update flow on main.
- **Dependencies:** Phase 4.
- **Risks:** secrets unavailable on fork PRs (skip judge metrics gracefully);
  judge flakiness (retry + cache).
- **Success criteria:** a deliberately degraded prompt turns the PR check red;
  reverting turns it green.
- **Estimated effort:** 3–5 h.

### Phase 6 — Model comparison
- **Goal:** benchmark many models on the same dataset; output a leaderboard.
- **Deliverables:** Anthropic / Gemini / HF-local adapters + factory; model
  config YAML library (incl. Ollama Qwen and mimik smollm2); `benchmark_runner`;
  leaderboard report; nightly matrix.
- **Dependencies:** Phase 4 (Phase 5 for automation).
- **Risks:** pricing drift (pricing lives in versioned YAML); local models
  can't run on hosted CI (benchmark locally, upload artifact).
- **Success criteria:** one command produces a leaderboard across ≥4
  providers, with smollm2-360m as the anchor row tied to the 3/10 baseline.
- **Estimated effort:** 4–6 h.

### Phase 7 — Reporting dashboard
- **Goal:** quality trends over time, visible without reading JSON.
- **Deliverables:** run-history aggregation; static HTML dashboard (metric
  trends per commit, leaderboard snapshots, per-category heatmap) published
  via GitHub Pages or artifacts.
- **Dependencies:** Phases 5–6.
- **Risks:** scope creep — stays a generated static page, never a service.
- **Success criteria:** dashboard shows ≥2 weeks of history and one
  model-comparison snapshot.
- **Estimated effort:** 4–8 h.

---

## Progress Tracker

### Phase 1 — Repository preparation (complete — awaiting review)
- [x] `deepeval` branch created from `main`
- [x] ROADMAP.md, ARCHITECTURE.md, DECISIONS.md, LEARNING_GUIDE.md created
- [x] `llm_client.chat()` — generation controls + client/model injection
- [x] `config.py` + `.env.example` — `LLM_TEMPERATURE` / `LLM_SEED` /
      `LLM_MAX_TOKENS`
- [x] `qa_expert.answer()` returns `AgentResult`; CLI + golden harness updated
- [x] Full test suite green (64 tests); ruff check + format clean
- [x] Branch pushed; draft PR opened against `main`
- [x] Documentation synced to completed work

### Remaining phases
- [ ] Phase 2 — Evaluation harness skeleton
- [ ] Phase 3 — Golden dataset v2
- [ ] Phase 4 — Full metric suite
- [ ] Phase 5 — CI integration
- [ ] Phase 6 — Model comparison
- [ ] Phase 7 — Reporting dashboard

---

## Maintenance Rules

At the end of every phase:

1. Tick the phase's checkboxes above and move the "CURRENT PHASE" marker.
2. Update ARCHITECTURE.md — mark planned components as implemented, correct
   any drift between design and reality.
3. Add ADR entries to DECISIONS.md for every significant decision made during
   the phase, including deviations from the audit (with reasons).
4. Extend LEARNING_GUIDE.md with every new concept the phase introduced.
