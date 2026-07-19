# LEARNING GUIDE — AI Evaluation Engineering Handbook

A personal handbook for a QA Engineer transitioning into AI Quality
Engineering, written against *this* repository. Every concept explains: what
it is in plain English, why it matters, where it appears in this repo, a code
example from here, common mistakes, and where to read more.

Living document: every phase that introduces a new concept adds a section.
Concepts marked **(stub — expanded in Phase N)** get full treatment when the
code that uses them lands.

Companions: [ROADMAP.md](ROADMAP.md) · [ARCHITECTURE.md](ARCHITECTURE.md) ·
[DECISIONS.md](DECISIONS.md)

---

# Part 1 — AI Fundamentals

## What is an LLM?

A Large Language Model is a neural network trained on huge amounts of text to
predict the next token in a sequence. That's the whole trick: given "The
capital of France is", it predicts "Paris" because that continuation was
overwhelmingly likely in its training data. Everything that looks like
reasoning, answering, or explaining is next-token prediction running in a
loop.

- **Why it matters:** LLMs don't "know" things the way a database does — they
  produce *plausible* text. Plausible ≠ correct. That single fact is why the
  entire evaluation discipline exists, and why this project retrieves real
  ISTQB text instead of trusting the model's memory.
- **In this repo:** `smollm2-360m` served by mimik, called through
  [qa_agent/llm_client.py](qa_agent/llm_client.py). "360m" = 360 million
  parameters (the network's learned weights) — tiny by modern standards,
  which is why RESULTS.md shows confident-but-wrong answers.
- **Common mistake:** treating model output as a fact lookup. QA instinct
  transfers well here: an LLM is an *untrusted component* whose outputs need
  verification.
- **Read more:** Andrej Karpathy, "Intro to Large Language Models" (YouTube);
  Jay Alammar, "The Illustrated Transformer".

## What is a prompt?

The text you send to the model. Chat models take a list of messages with
roles: a **system** message (standing instructions: persona, rules, output
format) and **user** messages (the actual request).

- **Why it matters:** the prompt is the model's *specification*. In this
  project it's literally a versioned spec file, and later phases will test
  the model against that spec — requirements-based testing, applied to AI.
- **In this repo:** the system prompt is
  [qa_agent/prompts/qa_expert.txt](qa_agent/prompts/qa_expert.txt) — persona
  ("Senior QA Engineer, 15+ years"), grounding rule ("Answer ONLY using
  information found in those context blocks"), the five-part answer
  structure, and citation rules. The user message is assembled in
  `qa_expert._build_user_message()`: numbered context blocks + the question.
- **Common mistake:** assuming instructions are obeyed. A prompt is a
  request, not a constraint — RESULTS.md shows smollm2 ignoring the
  five-part format completely. That gap between instruction and behavior is
  exactly what metrics measure.

## What is context (and a context window)?

Everything the model can see for the current request: system prompt + user
message (+ prior conversation, if any). The **context window** is the hard
limit on how much fits, measured in tokens.

- **Why it matters:** the model cannot use what isn't in the window, and
  overflowing the window fails or silently truncates.
- **In this repo:** smollm2-360m has a ~2K-token window. Four 500-word
  chunks + system prompt + question overflowed it (a real `llama_decode()`
  failure — see TODO.md Post-Step-9), which is why `top_k` was reduced to 2
  in [qa_agent/config.py](qa_agent/config.py). There's also a size guard:
  `_PROMPT_WORD_WARN_THRESHOLD = 1500` in
  [qa_agent/agents/qa_expert.py](qa_agent/agents/qa_expert.py).
- **Common mistake:** "more context is always better." Irrelevant context
  dilutes attention and invites hallucination; retrieval quality beats
  retrieval quantity.

## What is a token?

The unit models actually read and write — subword pieces, not words.
"metamorphic" might be 3–4 tokens; common words are usually one. Rule of
thumb for English: 1 token ≈ 0.75 words.

- **Why it matters:** context limits, pricing, and latency are all counted
  in tokens.
- **In this repo:** an honest engineering compromise — `chunker.py` splits
  by *words* while calling the setting `chunk_size` (500), and the logs say
  `words_in=` precisely because a word count is not a token count (TODO.md
  tracks this; an earlier log label `tokens_in` was renamed for honesty).
  `scripts/token_count.py` exists for real token diagnostics.
- **Common mistake:** doing capacity math in words or characters, then being
  surprised by overflow.

## What is inference?

Running the trained model to produce output (as opposed to *training*, which
updates weights). Every `qa-agent ask` triggers one inference request.

- **Why it matters for evaluation:** inference costs time and (for cloud
  models) money per token. An evaluation run is potentially hundreds of
  inference calls: dataset size × models × judge calls. That arithmetic
  shapes the whole CI design (smoke subset on PRs, full run nightly).
- **In this repo:** `llm_client.chat()` is the single inference gateway —
  one choke point for timeout, retry, and (later) usage capture.

## What is temperature?

A sampling knob controlling randomness. The model produces a probability
distribution over next tokens; temperature reshapes it before picking.
`0` ≈ always take the most likely token (near-greedy); higher values spread
probability toward less likely tokens (more varied, more creative, more
error-prone).

- **Why it matters for evaluation:** at high temperature the same question
  yields different answers on every run — scores move without any code
  change. Evaluation wants `temperature=0` so score changes mean *quality*
  changes, not dice rolls.
- **In this repo (Phase 1):** `llm_temperature` in
  [qa_agent/config.py](qa_agent/config.py) and the `temperature` parameter
  of `llm_client.chat()`. Deliberately `None` by default = "don't send it",
  preserving historical runtime behavior; the eval runner will pass `0.0`
  explicitly (see DECISIONS.md ADR-005).
- **Common mistake:** believing `temperature=0` makes output fully
  deterministic. It removes *sampling* randomness, but batching effects and
  floating-point nondeterminism on the server can still produce tiny
  variations.

## What is seed?

The initializer for the random number generator used during sampling. Same
prompt + same parameters + same seed on the same backend → the same "random"
choices, hence (ideally) the same output.

- **Why it matters:** reproducibility. A CI failure you can't reproduce
  locally is a flake, and flakes are the death of quality gates — the QA
  version of this lesson needs no explanation.
- **In this repo (Phase 1):** `llm_seed` in config, `seed` parameter in
  `chat()`. Off (`None`) by default.
- **Common mistake:** trusting the seed everywhere — support varies by
  backend (OpenAI treats it as best-effort; local runtimes vary). Belt and
  suspenders: seed **plus** temperature 0 **plus** averaging over enough
  cases.

## What is max_tokens?

A cap on how many tokens the model may generate in its reply.

- **Why it matters:** bounds cost and latency, and prevents runaway
  rambling — a real risk with small models. For fair model comparison, every
  candidate should get the same generation budget.
- **In this repo (Phase 1):** `llm_max_tokens` in config, `max_tokens` in
  `chat()`. `None` = server default (today's behavior).
- **Common mistake:** setting it too low and then evaluating truncated
  answers — the metric will punish the cutoff, not the model's ability.

## What is deterministic generation?

The practice of pinning every randomness source — temperature 0, fixed seed,
same model version, same parameters — so identical inputs produce identical
(or near-identical) outputs.

- **Why it matters:** it is the *precondition for regression testing an LLM*.
  Without it you cannot distinguish "my change made quality worse" from
  "the dice landed differently." RESULTS.md's Non-determinism section
  documents exactly this pain: same questions, materially different wrong
  answers per run.
- **In this repo:** the Phase 1 `temperature`/`seed`/`max_tokens` plumbing
  exists precisely so evaluation runs can pin these. Residual variance that
  can't be pinned is handled statistically (thresholds on averages across
  30+ cases, not single-case pass/fail).

---

# Part 2 — RAG (Retrieval-Augmented Generation)

## What is RAG, and why retrieval is needed

RAG = look up relevant documents first, then have the model answer *from
those documents* instead of from memory. Two stages: **retrieval** (find the
top-k most relevant chunks for the question) and **generation** (answer
grounded in them).

- **Why it matters:** it converts "trust the model's memory" into "trust the
  provided sources" — hallucination control, source citations, and the
  ability to use private/current documents the model never saw in training.
- **In this repo:** the entire query pipeline.
  [qa_agent/agents/qa_expert.py](qa_agent/agents/qa_expert.py) retrieves
  from ChromaDB, gates on similarity score, builds context blocks, and only
  then calls the LLM. The system prompt forbids answering from training
  knowledge.
- **Common mistake:** blaming the generator when retrieval was wrong. If the
  right chunk never arrived, the best model in the world answers badly.
  CLAUDE.md encodes the fix as a rule: *"if answers are wrong, inspect
  retrieved chunks first, prompt second."* That's why the future metrics
  score retrieval and generation separately.

## Embeddings

An embedding model converts text into a vector (list of numbers, here 384 of
them) where *similar meaning → nearby vectors*. "How do I test an ML model?"
and "validation of machine learning systems" end up close together despite
sharing almost no words.

- **In this repo:** [qa_agent/embeddings.py](qa_agent/embeddings.py) wraps
  `sentence-transformers/all-MiniLM-L6-v2`, batched (never one-at-a-time in
  a loop — an ingestion performance rule from CLAUDE.md).
- **Common mistake:** mixing embedding models — vectors from different
  models live in incompatible spaces. Query and corpus must use the same
  model; changing it means re-ingesting everything.
- **Read more:** sentence-transformers docs; "Sentence-BERT" paper.

## Vector databases & similarity search

A vector DB stores embeddings and answers "which stored vectors are closest
to this query vector?" efficiently. Closeness here is **cosine similarity**
(angle between vectors). This repo converts ChromaDB's cosine *distance* to
a similarity score: `score = 1 − distance` (see `vector_store.query()`), so
higher = more similar.

- **In this repo:** [qa_agent/vector_store.py](qa_agent/vector_store.py) —
  persistent ChromaDB collection, cosine space, provenance metadata
  (`source_doc`, `page`, `chunk_id`) stored per chunk. That metadata powers
  citations today and citation *checking* in Phase 4.
- **The abstain gate:** if the best score is below `abstain_threshold`
  (0.35), the agent refuses instead of guessing — the single most
  QA-engineer-shaped behavior in the system, and the one thing the v1 golden
  suite proved works (3/3 abstain cases passed).
- **Common mistake:** treating the similarity score as a calibrated
  confidence. It's relative, embedding-model-specific, and phrasing-
  sensitive — RESULTS.md q04 shows a *grammatically mangled* question
  dropping below threshold while a clean phrasing would have passed.

## Chunking

Splitting documents into retrieval-sized pieces. Too big: chunks blow the
context window and bury the relevant sentence. Too small: chunks lose the
surrounding meaning. Overlap between consecutive chunks prevents a concept
from being cut in half at a boundary.

- **In this repo:** [qa_agent/chunker.py](qa_agent/chunker.py) — ~500 words
  per chunk, 100-word overlap, word-based splitting (a known approximation,
  see TODO.md), each chunk stamped with page and a content-hash `chunk_id`.
- **Common mistake:** tuning chunk size by feel. The repo's rule is better:
  don't tune retrieval parameters until the golden suite gives you a stable
  baseline to measure the change against.

---

# Part 3 — Evaluation

## Why exact string matching doesn't work

Two answers can be worded completely differently and both be correct — or
share every keyword and mean opposite things. Classic assertion-style QA
(`assert actual == expected`) is built for deterministic systems; LLM output
is open-ended natural language.

- **In this repo — the receipts:** [tests/golden/scoring.py](tests/golden/scoring.py)
  is keyword matching, and [RESULTS.md](RESULTS.md) documents both failure
  directions. smollm2 said "metamorphic testing" (keyword pass!) while
  describing something entirely wrong (concept fail). The Observations
  section explicitly lists what keyword matching cannot see: semantic drift,
  citation accuracy, coherence. That paragraph is the origin story of this
  whole DeepEval effort.
- **The QA translation:** you're moving from `assertEquals` to *judged
  acceptance criteria* — closer to how you'd review a junior tester's
  written answer than how you'd assert on a function's return value.

## What is DeepEval and why it exists

An open-source Python framework for testing LLM applications, built to feel
like pytest: you build test cases (input, actual output, expected output,
retrieval context), attach metrics with thresholds, and get pass/fail plus
scores and reasons. It exists because everyone was hand-rolling the same
judge prompts, scoring loops, and report generators — DeepEval standardizes
that layer (see DECISIONS.md ADR-001 for why we chose it over alternatives).

- **In this repo:** arrives in Phase 2 as an eval-only dependency; `qa_agent/`
  will never import it.

## What is a Golden Dataset?

A fixed, versioned set of inputs with expected outcomes — the LLM world's
regression suite. "Golden" = these are the blessed reference cases.

- **In this repo:** v1 is [tests/golden/golden_set.json](tests/golden/golden_set.json)
  (10 cases: 7 concept questions with keywords, 3 abstain triggers). Phase 3
  builds v2: JSONL with real reference answers (`expected_answer`), atomic
  `ground_truth_facts`, expected retrieval pages, difficulty/category/tags
  for slicing, and frozen contexts (explained below).
- **Common mistakes:** letting the dataset go stale as the product evolves;
  writing only easy cases; skipping *negative* cases. The v1 set's abstain
  triggers (sourdough bread, hockey scores) are genuinely good negative-case
  design — they test what the system should *refuse* to do.

## Judge models and LLM-as-a-Judge

Using a strong LLM to grade another LLM's output against criteria — because
semantic quality ("is this answer faithful to the source?") is a judgment
call, and human judgment doesn't scale to every commit.

- **How it works:** the judge gets the question, the candidate answer, the
  reference/context, and a rubric; it returns a score and reasoning.
  DeepEval wraps this pattern for each metric.
- **Rules of thumb:** the judge must be *stronger* than the candidates
  (never judge with a model weaker than what you're grading); pin the judge
  version (a judge upgrade shifts every score — that's a measurement-system
  change, the ML version of recalibrating your test instruments); spot-check
  the judge against your own expert judgment before trusting thresholds.
- **In this repo:** judge choice is configurable (Phase 4, through the same
  model-adapter layer). Note the irony budget: we evaluate an LLM with an
  LLM, which is why the plan also includes *deterministic* metrics that need
  no judge at all.

## The metrics we will use (Phase 4)

**Answer Relevancy** — does the answer actually address the question?
Catches topic drift (smollm2's dominant failure: fluent paragraphs about the
wrong thing). Threshold ≥ 0.80 average.

**Faithfulness** — is every claim in the answer supported by the retrieved
context? This is the system prompt's core rule ("Answer ONLY using the
context blocks") turned into a number. Threshold ≥ 0.90 — the highest bar,
because grounding is this product's entire promise.

**Hallucination** — the mirror image: how much of the answer contradicts or
invents beyond the provided context? Threshold ≤ 0.10 (lower is better —
note the inverted direction; a classic reporting mistake is reading it
backwards).

**Contextual Precision / Recall** — retrieval-side metrics. Precision: of
the chunks retrieved, how many were relevant (and ranked well)? Recall: of
the chunks *needed*, how many were retrieved? These run in live-retrieval
mode only, because frozen contexts hold retrieval constant by design.

**G-Eval** — DeepEval's "write your own rubric" metric: you describe
criteria in natural language and the judge scores against them. We'll use it
for the contracts unique to this project: *ISTQB terminology usage* and
*five-part answer format compliance* — both are rules in
`prompts/qa_expert.txt` that today go completely unmeasured.

**Custom deterministic metrics** — plain Python, no judge, no tokens, no
flakiness:
- *Abstain Correctness*: abstain cases must return exactly
  `ABSTAIN_MESSAGE`; answerable cases must NOT abstain. Hard gate = 1.0.
- *Citation Validity*: every inline `[page N]` must cite a page actually
  present in the retrieved chunks (provenance metadata makes this checkable).

**Deferred honestly:** Tool Correctness, Task Completion, plan-quality
metrics, Conversation Completeness — this agent has no tools, no planner,
and no multi-turn memory (explicit non-goals). Measuring nonexistent
capabilities produces theater, not quality data. The dataset schema reserves
the fields for future agents. **(stub — expanded if/when a tool-using agent
exists)**

---

# Part 4 — Architecture Concepts

## Why AgentResult exists (Phase 1)

Before: `answer()` returned a string; retrieval scores, prompts, and timing
were logged and thrown away. Evaluation needs those as *data*, not log
lines: DeepEval's test case wants `input`, `actual_output`, and
`retrieval_context`.

`AgentResult` (in [qa_agent/agents/qa_expert.py](qa_agent/agents/qa_expert.py))
carries: the answer, the retrieved hits (with scores and provenance), the
`abstained` flag, both prompts, the model name, and latency. The CLI prints
`result.answer` — user-visible behavior unchanged.

- **QA translation:** it's the difference between a test that prints "FAIL"
  and a test that attaches the full request/response trace. You already know
  which one you can debug.
- **Common mistake elsewhere:** scraping logs for evaluation data — fragile
  coupling to log formats. Return values are the honest interface
  (DECISIONS.md ADR-003).

## Why dependency injection matters (Phase 1)

`llm_client.chat()` used to construct its one-and-only client internally —
no way to point the same agent at a different model without editing config
globally. Now `chat(..., client=…, model=…)` accepts an injected client;
default behavior is untouched.

- **Why:** model comparison means running the *identical agent code path*
  against N backends. Injection is the seam that makes the backend a
  parameter instead of a hardcoded fact.
- **QA translation:** it's testability 101 — the same reason you inject a
  database connection instead of newing it up in the method: so tests (or
  benchmarks) can substitute the dependency.
- **Common mistake:** monkeypatching internals instead of adding a seam —
  works until the internal changes, then everything breaks at once.

## Why model adapters and abstraction layers (Phases 2 & 6)

Different providers have different SDKs, auth, parameter names, and quirks
(Anthropic takes the system prompt as a top-level field, not a message; a
first token from Ollama may take 30 s while the model loads). An **adapter**
per provider family normalizes all of that behind one `ChatModel.generate()`
interface; a **factory** builds the right adapter from a YAML config.
Everything above the adapter layer is provider-blind — which is precisely
the "evaluation must not depend on one provider" requirement, enforced by
structure rather than discipline.

Bonus insight that keeps this cheap: OpenAI, Ollama, vLLM, and mimik all
speak the same OpenAI-compatible wire protocol — one adapter, four runtimes,
different `base_url` (ADR-007).

## Why benchmark multiple models (Phase 6)

Model choice is currently a guess constrained by hardware. A benchmark run —
same dataset, same judge, temperature 0, frozen contexts — turns it into a
table: quality per metric, latency, cost. RESULTS.md already predicts the
first experiment's outcome ("a 3B+ model would improve concept correctness
substantially"); the leaderboard replaces that prediction with a
measurement, anchored to the published smollm2 3/10 baseline.

## Why frozen-context evaluation exists (Phase 3)

The ISTQB PDFs are copyrighted and gitignored; CI can never rebuild the
vector store. Frozen contexts = capture each case's retrieved chunks once
locally, commit small excerpts, and have CI replay them. Two birds: CI
becomes possible, *and* generation is isolated from retrieval variance —
which is exactly what a fair model comparison needs anyway (ADR-006).

- **The trade:** CI doesn't exercise the retriever; live-retrieval runs
  cover that locally/nightly.
- **QA translation:** it's a recorded test double — same reasoning as
  replaying recorded API responses when the real dependency isn't available
  in CI.

## Why CI should run evaluations (Phase 5)

A quality bar that isn't enforced automatically erodes — you've watched this
happen with flaky test suites and optional lint. LLM quality is *worse*: a
one-word prompt edit can silently degrade answers with zero code diff to
review. Per-PR evaluation (small smoke subset, cents per run) plus nightly
full runs makes quality regressions as visible as compile errors, with the
threshold file (`eval.yaml`) reviewable like any other code.

---

# Part 5 — Concepts Added During Implementation

## DeepEval's LLMTestCase anatomy (Phase 2)

`LLMTestCase` is the unit DeepEval metrics consume — think of it as the
"test fixture" for one evaluated interaction:

- `input` — the question asked (our golden case's `question`).
- `actual_output` — what the agent produced (`AgentResult.answer`).
- `expected_output` — the reference answer, when one exists (optional;
  ours arrive in Phase 3).
- `retrieval_context` — the chunks the agent was actually given (we map
  `AgentResult.retrieved` texts here). Faithfulness and Hallucination
  judge the answer *against this*, which is why Phase 1's trace capture
  was a prerequisite.

**In this repo:** the mapping lives in one place —
`evaluation/runners/agent_runner.py::to_llm_test_case()`. **Common
mistake:** putting the *whole corpus* in `retrieval_context` instead of
what the agent actually saw — that measures a system that doesn't exist.

## Poetry dependency groups (Phase 2)

`[tool.poetry.group.eval.dependencies]` keeps DeepEval (and its ~30
transitive packages) out of the runtime footprint conceptually: the
agent needs none of it, and `poetry install --without eval` gives a
lean install. **In this repo:** `pyproject.toml`, group `eval`
(deepeval, pyyaml). Same idea as the existing `dev` group for
pytest/ruff.

## Reading your first eval run (Phase 2)

The first live run is worth studying —
`evaluation/outputs/<run_id>/` from the q01 verification run:

- `scores.json` → answer relevancy mean 0.67 (threshold 0.80 → FAIL).
- `cases.jsonl` → full trace: retrieval scores [0.42, 0.39], not
  abstained, 15 s latency, the exact prompts.
- `run_meta.json` → judge model recorded — this run used the weak local
  judge, so per DECISIONS.md ADR-013 the *number* is not quality
  evidence; the *plumbing* it proves is.

The failure itself is the system working: smollm2 answered about
"systems adapting to changing user needs" — topic drift the old keyword
harness scored as a terminology PASS, but the relevancy judge punished.

Still to come:

- **(stub — Phase 3)** Dataset governance: review checklists, versioning,
  category/difficulty slicing.
- **(stub — Phase 4)** Judge calibration, verdict caching, baseline vs
  threshold gating, regression epsilon.
- **(stub — Phase 5)** GitHub Actions for eval: secrets, caching, artifact
  strategy, fork-PR handling.
- **(stub — Phase 6)** Cost accounting per provider; composite scoring and
  weight selection; latency measurement pitfalls across hardware.
- **(stub — Phase 7)** Trend analysis: why slow drift hides in single runs.

## Recommended general resources

- DeepEval documentation (confident-ai.com/docs) — metrics reference.
- "Your AI Product Needs Evals" — Hamel Husain (essay; the practitioner
  case for everything this project is doing).
- OpenAI / Anthropic evaluation guides (both vendors' docs have solid
  eval-design sections).
- Chip Huyen, *AI Engineering* (O'Reilly, 2025) — evaluation chapters.
- The ISTQB CT-AI syllabus itself — you're building the tooling it
  describes: this project *is* AI testing practice.
