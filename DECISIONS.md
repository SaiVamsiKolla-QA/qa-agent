# DECISIONS — Architecture Decision Records

One numbered entry per significant technical decision. Format: Decision /
Context / Alternatives considered / Why this option / Trade-offs / Future
implications. Newest entries appended at the bottom. This document grows as
the project evolves — every phase that makes a real choice adds an ADR,
including any deviation from the approved audit.

Companions: [ROADMAP.md](ROADMAP.md) · [ARCHITECTURE.md](ARCHITECTURE.md) ·
[LEARNING_GUIDE.md](LEARNING_GUIDE.md)

---

## ADR-001 — Use DeepEval for LLM evaluation

- **Decision:** adopt DeepEval as the evaluation framework, added as a
  dev/eval dependency only (never imported by `qa_agent/`).
- **Context:** the v1 golden harness scores answers by keyword substring
  matching. RESULTS.md documents its blind spots: semantic drift, citation
  accuracy, answer coherence, usefulness of suggested test cases. The
  project goal is per-commit, threshold-gated quality measurement plus model
  comparison.
- **Alternatives:** hand-rolled LLM-as-judge scripts (maximum learning, but
  we'd rebuild test-case models, metric prompts, thresholds, caching, and
  reporting that DeepEval ships); Ragas (RAG-focused but weaker
  pytest/threshold/CI ergonomics); promptfoo (config-driven, JS ecosystem,
  weaker Python integration); LangSmith/braintrust (hosted, conflicts with
  local-first ethos).
- **Why DeepEval:** pytest-native (matches the repo's testing culture),
  ships the exact metrics we need (Answer Relevancy, Faithfulness,
  Hallucination, contextual metrics, G-Eval), supports custom metrics and
  configurable judge models, and is a harness — not an orchestration
  framework, so it does not violate the spirit of CLAUDE.md's no-framework
  rule (that rule protects learning how *agents* work; evaluation is a new
  layer we are learning on purpose).
- **Trade-offs:** a real dependency with its own release cadence; judge
  metrics cost tokens and introduce variance.
- **Future implications:** CLAUDE.md's forbidden-tools list gets an explicit
  DeepEval allowance in Phase 2; judge model choice becomes a config concern
  (ADR-007 territory when it lands).

## ADR-002 — Golden dataset as the quality contract

- **Decision:** a versioned, reviewed golden dataset (JSONL) is the single
  definition of expected agent behavior; every evaluation and benchmark runs
  against it.
- **Context:** without a fixed dataset, scores are not comparable across
  commits or models; the existing 10-question set proved the concept but
  lacks reference answers.
- **Alternatives:** ad-hoc manual testing (not reproducible); synthetic
  LLM-generated datasets (fast but encode the generator's biases, defeating
  the "QA expert judgment" moat); live user traffic (none exists).
- **Why:** deterministic, diffable, reviewable like code; the same file
  serves per-commit gating *and* cross-model benchmarking, which is a stated
  project goal.
- **Trade-offs:** authoring reference answers is real domain work; the
  dataset can overfit to itself over time (mitigate by growing it and
  slicing by category).
- **Future implications:** dataset changes require the same review rigor as
  code; version field invalidates stale baselines.

## ADR-003 — `AgentResult` structured return

- **Decision:** `qa_expert.answer()` returns a frozen `AgentResult`
  dataclass (`answer`, `retrieved`, `abstained`, `system_prompt`,
  `user_message`, `model_name`, `latency_s`) instead of a bare string.
- **Context:** DeepEval's `LLMTestCase` needs `input`, `actual_output`, and
  `retrieval_context`. Before this change the agent logged retrieval scores
  and prompts, then threw them away — evaluation would have had to re-derive
  or scrape logs.
- **Alternatives:** parse logs (fragile, couples eval to log format); a
  parallel `answer_with_trace()` function (two code paths to keep in sync);
  global trace collector (hidden state, violates repo principles).
- **Why:** the return value is the honest interface; one code path; CLI
  behavior preserved by printing `result.answer`.
- **Trade-offs:** touched every caller (CLI, unit tests, golden harness,
  `scripts/run_golden.py`) in one commit.
- **Future implications:** token/cost fields can be added later without
  another breaking change; future agents should return the same shape.

## ADR-004 — Dependency injection in `llm_client`

- **Decision:** `chat()` accepts optional keyword-only `client` and `model`
  arguments, defaulting to the mimik client and `settings.model_name`.
- **Context:** model comparison requires running the *same agent* with
  different backends; the client was constructed inside `chat()` with no
  seam.
- **Alternatives:** monkeypatching in eval code (works for tests, gross for
  a product feature); environment-variable swapping per run (process-global,
  precludes in-process benchmarking of several models); a full provider
  class hierarchy inside `qa_agent` (framework-shaped, violates learning
  goals — belongs in `evaluation/models/` instead).
- **Why:** smallest possible seam; default path byte-identical to before;
  the future adapter layer plugs in here without `qa_agent` knowing it
  exists.
- **Trade-offs:** slightly wider function signature.
- **Future implications:** `evaluation/models/factory.py` (Phase 2/6) builds
  clients and passes them through this seam.

## ADR-005 — Generation parameters default to `None` (omit), not `0.0`
  *(deviation from the audit's first draft)*

- **Decision:** `temperature`, `seed`, `max_tokens` exist in config and
  `chat()`, but default to `None`, meaning the parameter is **not sent** in
  the request.
- **Context:** the audit originally suggested defaulting temperature to 0
  for determinism. But today's runtime sends no generation parameters — the
  server default applies — and Phase 1's contract is "zero behavior change."
- **Alternatives:** default `temperature=0.0` (silently changes runtime
  answer behavior); hardcode determinism only in eval code (leaves the
  runtime knob undocumented).
- **Why:** `None` preserves today's requests exactly; determinism becomes an
  explicit choice the eval runner makes (`temperature=0.0, seed=42`) rather
  than a hidden default.
- **Trade-offs:** evaluation must remember to pass the values (enforced
  later in `eval.yaml` defaults).
- **Future implications:** when the runtime model is upgraded, choosing a
  production temperature becomes a deliberate, documented decision.

## ADR-006 — Frozen-context evaluation mode

- **Decision:** capture each golden case's retrieved chunks once locally,
  commit them as small excerpts, and let CI evaluate generation quality by
  replaying them (`--mode frozen-context`); retrieval quality is evaluated
  only where the real corpus exists (`--mode live-retrieval`).
- **Context:** ISTQB PDFs and `chroma_db/` are gitignored for copyright
  reasons — hosted CI can never rebuild the vector store. Without a
  workaround, "run eval on every commit" is impossible.
- **Alternatives:** commit the ChromaDB (still contains copyrighted text —
  same problem, worse form); private artifact storage for the corpus
  (infrastructure + licensing questions); self-hosted runner with corpus
  (single point of failure, defer); CI-skip evaluation entirely (defeats the
  goal).
- **Why:** small quoted excerpts per question are the minimal footprint that
  makes CI possible; it also isolates the generator from retrieval noise,
  which is exactly what fair model benchmarking needs.
- **Trade-offs:** CI does not exercise the retriever (covered by
  local/nightly live-retrieval runs); frozen contexts can go stale if the
  corpus or chunking changes (dataset version bump forces recapture).
- **Future implications:** a self-hosted runner later unlocks live-retrieval
  in CI; excerpt size stays deliberately minimal.

## ADR-007 — Model adapters + provider abstraction (one OpenAI-compatible adapter)

- **Decision:** a `ChatModel` protocol with adapter classes per provider
  *family*, built by a factory from per-model YAML configs. One
  `OpenAICompatibleAdapter` covers OpenAI, Ollama, vLLM, mimik, and LM
  Studio (same wire protocol, different `base_url`); Anthropic, Gemini, and
  local HuggingFace get dedicated adapters. GGUF models are served through
  Ollama rather than a bespoke llama.cpp adapter.
- **Context:** requirement — evaluation must not depend on one provider;
  candidates span cloud APIs and local runtimes.
- **Alternatives:** LiteLLM (one dependency abstracts everything — but
  hides exactly the mechanics this learning project exists to expose);
  if/else on provider name inside the runner (couples eval logic to SDKs);
  per-model subprocess CLIs (unmeasurable latency/cost).
- **Why:** the adapter pattern makes provider knowledge a leaf concern;
  exploiting OpenAI-compatibility keeps the adapter count at four for
  seven-plus runtimes; YAML configs make "add a model" a no-code operation.
- **Trade-offs:** we maintain thin SDK wrappers ourselves; token/cost
  accounting differs per provider and lives in the adapters.
- **Future implications:** the judge model uses the same abstraction, so
  judge choice is also provider-agnostic; secrets stay env-var-only
  (`api_key_env` in YAML names the variable, never holds the value).

## ADR-008 — Benchmark multiple models under fairness invariants

- **Decision:** `benchmark_runner` loops the standard `eval_runner` over N
  model configs with identical dataset version, identical pinned judge,
  temperature 0, and frozen contexts, then emits a leaderboard (composite +
  per-metric + latency + cost) with `smollm2-360m` as the permanent anchor
  row.
- **Context:** project goal #2 is evidence-based model choice; RESULTS.md
  explicitly names "re-run this harness against a larger model" as the next
  experiment.
- **Alternatives:** public leaderboards (don't measure *our* task); one-off
  manual comparisons (not reproducible).
- **Why:** reusing `eval_runner` guarantees every model is measured by the
  same code path; frozen contexts hold retrieval constant so the comparison
  isolates the generator; the anchor row ties every future leaderboard to
  the published 3/10 baseline.
- **Trade-offs:** local models can't run on hosted CI (benchmarked locally,
  results uploaded as artifacts); cross-hardware latency numbers are not
  directly comparable (hardware recorded in run metadata).
- **Future implications:** composite weights live in `eval.yaml` and are
  themselves an ADR when first tuned.

## ADR-009 — `evaluation/` folder structure, separate from `qa_agent/`

- **Decision:** all evaluation code lives in a top-level `evaluation/`
  package (`datasets/ models/ runners/ metrics/ configs/ baselines/
  outputs/ reports/`); `qa_agent/` is imported only by
  `runners/agent_runner.py`.
- **Context:** the SUT is a deliberately small learning codebase with strict
  layer rules; evaluation is a second concern with its own dependencies.
- **Alternatives:** grow `tests/golden/` into the framework (conflates
  "tests of the code" with "evaluation of the model", and pytest is the
  wrong shape for benchmark orchestration); a separate repository (dataset,
  SUT, and eval must version together — cross-repo sync pain).
- **Why:** clean dependency direction (evaluation → agent, never the
  reverse); each folder has one responsibility; `outputs/` vs `reports/`
  separates replayable raw traces from human-readable summaries; committed
  `baselines/` enables regression gating, not just absolute thresholds.
- **Trade-offs:** some scaffolding before the first metric runs (Phase 2 is
  deliberately "one case, one metric, end-to-end").
- **Future implications:** DeepEval and provider SDKs go in a Poetry
  `[eval]` dependency group so the runtime install stays lean.

## ADR-010 — JSONL for the golden dataset

- **Decision:** golden dataset v2 is JSON Lines (one case per line),
  validated by a pydantic schema at load time.
- **Context:** the v1 set is a single JSON array; the dataset will grow to
  30–50+ cases and be edited in PRs.
- **Alternatives:** single JSON array (whole-file diffs, merge conflicts);
  YAML (friendlier to write, but multiline reference answers + significant
  whitespace invite silent errors); CSV (can't hold nested fields); a
  database (overkill, not diffable).
- **Why:** line-per-case diffs make PR review of dataset changes readable;
  streams naturally; standard format for eval sets; schema validation turns
  malformed cases into load-time errors instead of silently skewed scores.
- **Trade-offs:** slightly less human-friendly to hand-edit than YAML.
- **Future implications:** case `id` + dataset `version` are the join keys
  for baselines, history, and leaderboards.

## ADR-011 — Golden-harness updates ride along with the AgentResult commit

- **Decision:** `tests/golden/test_rag_quality.py` and
  `scripts/run_golden.py` were updated to read `.answer` in the *same
  commit* that changed `answer()`'s return type — not in a separate cleanup.
- **Context:** the audit's Phase 1 task list named CLI and unit tests as the
  blast radius; re-validation before implementation found the golden harness
  and results script also consume `answer()` as a string.
- **Alternatives:** leave them broken until Phase 3 rewrites them (the repo
  would carry a broken harness and the 3/10 baseline would become
  unreproducible); a compatibility shim returning strings (two interfaces).
- **Why:** every commit leaves the repo fully working (repo quality-gate
  rule), and the v1 baseline stays reproducible until v2 supersedes it.
- **Trade-offs:** a slightly larger commit.
- **Future implications:** none — v1 harness files retire in Phase 3/4, and
  this ADR documents why they survived Phase 1 intact.
