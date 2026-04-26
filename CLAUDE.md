# CLAUDE.md

Instructions for Claude Code when working in this repo. Read this before making changes.

## Project Mission
Build a local QA Expert Agent that reads ISTQB certification material and behaves like a Senior QA mentor. This is a **learning project** — the goal is to practice Python, end-to-end RAG, and agentic patterns built from primitives. Runs fully on mimik AI Foundation to dogfood the runtime while learning the mechanics underneath.

## Current Status
**Steps 1–9 complete. Step 10 (golden test suite) remaining.**

All implementation steps are complete and committed:
- Steps 1–2: `pyproject.toml`, `config.py`, and their tests — confirmed passing.
- Step 3: `cli.py` (ping subcommand) + `llm_client.py` + `test_llm_client.py` — mimik auth wired through config.
- Step 4: `pdf_loader.py` + `test_pdf_loader.py` — 8 tests pass.
- Step 5: `chunker.py` + `test_chunker.py` — 12 tests pass.
- Step 6: `embeddings.py` + `test_embeddings.py` — 6 tests pass (real all-MiniLM-L6-v2, no mocking).
- Step 7: `vector_store.py` + `tests/unit/test_vector_store.py` — 9 tests pass (real ChromaDB, tmp_path-backed).
- Step 8: `ingest` subcommand in `cli.py` + `tests/integration/test_ingest.py` — 2 integration tests pass.
- Step 8b: provenance metadata (`source_doc`, `page`, `chunk_index`, `chunk_id`) added to chunks and stored in ChromaDB.
- Step 9: `agents/qa_expert.py`, `prompts/qa_expert.txt`, `ask` subcommand in `cli.py` + `tests/unit/test_qa_expert.py` — 4 unit tests pass. `qa-agent ask` returns grounded answers with abstain logic.
- 48 tests pass (46 unit + 2 integration). Lint clean (`ruff check .`).
- mimOE serves `smollm2-360m` on `localhost:8083`.
- ChromaDB holds 68 chunks of ISTQB CT-AI syllabus with full provenance metadata.

Remaining: Step 10 — implement golden test harness (≥10 Q&A pairs), run it, document results honestly.

**Known limitation:** `smollm2-360m` (360M params) is too small for reliable structured output. Step 10 results will reflect this. See Known Limitations section below.

*Update this section whenever the step changes. Current status drives what Claude Code should and should not work on.*

## Project Context
Solo-built by a Senior QA Engineer transitioning toward SDET and eventually ML engineering. Under 30 minutes of study time per weekday. Python experience is early-stage — optimize for learnable and legible, not clever. This repo doubles as a portfolio piece demonstrating agentic QA tooling on mimik. Because time is tight, scope discipline and review discipline matter more than feature ambition.

## Working With Claude Code
**This section takes precedence over any implicit "be helpful by doing more" behavior.** The user is actively learning Python and RAG mechanics. Generating multiple files in a single session — even when it would be faster — prevents that learning and leaves unreviewed code behind. Respect the following rules in every session.

- **One deliverable per step.** A step produces one source file, or one source file plus its test. Never more.
- **Stop after each step.** When a step is complete, stop generating and wait for the user to review, run, and confirm before starting the next step. Do not proactively begin the next step even if it seems obviously next.
- **Each step must be runnable.** The user must be able to execute something — a test, a CLI command, an import — and see output at the end of every step. Steps that cannot be run in isolation should be decomposed further.
- **Name the step at the top of every response.** Begin responses with "Step N: <deliverable>" so there is no ambiguity about scope.
- **Review checkpoints are non-negotiable.** If the user has not confirmed the previous step works, do not start the next step regardless of how trivial the next step seems.
- **If a prompt is ambiguous about scope, ask.** One clarifying question at the start is preferable to generating more than the user wanted.
- **When adding a new file, explain its responsibility in one sentence before writing code.** If that sentence overlaps with an existing file's responsibility, stop and raise the overlap rather than writing the file.

Canonical prompt shape the user will send, and the shape Claude Code should mirror back:

> "Step N: [one deliverable]. Do not start Step N+1. Stop when done and wait for me to run [exit test]."

## Tech Stack (Strict)
These are fixed. Do not substitute without explicit instruction.

- **Language:** Python 3.11+
- **Package manager:** Poetry (PEP 621 `[project]` metadata style)
- **LLM runtime:** mimik AI Foundation (local, OpenAI-compatible endpoint on `localhost:8083`)
- **LLM client library:** `openai` SDK pointed at the local mimik base URL
- **Model:** GGUF instruct model, Q4_K_M quantization. Default ~3B parameters; ~7B if host RAM ≥ 32 GB. Exact model name lives in `.env`.
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2`
- **Vector store:** ChromaDB (local persistent, `./chroma_db/`)
- **PDF parsing:** `pypdf`
- **Config:** `pydantic-settings`, loaded from `.env`
- **Testing:** `pytest`
- **Lint/format:** `ruff`
- **Interface:** CLI only until Phase 4

### Forbidden Tools
Do not add any of these without explicit approval in a PR description. This list exists to protect the learning goal — frameworks that hide RAG and agent mechanics are off-limits on purpose.

- **Agent / RAG frameworks:** LangChain, LlamaIndex, LangGraph, CrewAI, AutoGen, Smol-agents, Haystack, or any other orchestration framework.
- **Web frameworks before Phase 4:** FastAPI, Flask, Django, Starlette. FastAPI becomes allowed only from Phase 4 onward.
- **Cloud LLM endpoints:** OpenAI, Anthropic, Google, Mistral, Cohere. Local-only is a hard constraint. *Note:* using the OpenAI Python SDK pointed at localhost mimik is fine — the rule is about endpoints, not client libraries.
- **Heavyweight test runners:** no `unittest` boilerplate, no `nose`. `pytest` only.

## Architecture
Two pipelines, kept separate in code.

**Ingestion pipeline (offline, run once per PDF):**
```
PDF → pdf_loader → chunker → embeddings (batched) → vector_store.add_chunks()
```

**Query pipeline (runtime):**
```
User question → CLI → qa_expert agent → vector_store.query() → llm_client → mimik → answer
```

Repo layout:
```
qa-expert-agent/
├── qa_agent/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── llm_client.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── pdf_loader.py
│   ├── chunker.py
│   ├── prompts/
│   │   └── qa_expert.txt       # Step 9
│   └── agents/
│       └── qa_expert.py        # Step 9
├── data/
│   └── istqb_docs/             # gitignored
├── chroma_db/                  # gitignored
├── tests/
│   ├── unit/
│   ├── integration/
│   └── golden/                 # Step 10
├── pyproject.toml
├── .env.example
└── CLAUDE.md
```

## Retrieval Strategy
These parameters drive RAG quality. All of them live in `config.py` and are overridable via `.env`. Do not hardcode any of these values in agents or tools.

- **Chunk size:** 500 tokens (default). Valid range 500–800.
- **Chunk overlap:** 100 tokens.
- **Top-k retrieval:** 4.
- **Similarity metric:** cosine.
- **Tuning rule:** do not tune these parameters until the golden test suite (see Testing Strategy) has a stable baseline. Chase retrieval quality before prompt quality — if answers are wrong, inspect retrieved chunks first, prompt second.

## Layer Responsibilities

**Definitions — do not confuse these:**
- **Tools** = pure utility modules (`pdf_loader`, `chunker`, `embeddings`, `vector_store`, `llm_client`). Stateless where possible. They transform data. Tools do not call LLMs, except `llm_client` itself.
- **Agents** = orchestration layer that combines tools plus an LLM call to answer a query. Agents make decisions; tools only transform.

**Per-module responsibilities:**
- **`cli.py`** — user-facing I/O and argument parsing. `print()` allowed here and only here. Delegates all work to agents and tools. No business logic.
- **`config.py`** — loads environment, validates via pydantic-settings. Single source of truth for endpoints, model names, file paths, retrieval parameters.
- **`llm_client.py`** — sole gateway to mimik AI Foundation. Every LLM call goes through this module. Owns retry and timeout policy. Concrete endpoint: `POST http://localhost:8083/mimik-ai/openai/v1/chat/completions`. Do not invent variants.
- **`embeddings.py`** — wraps sentence-transformers. Stateless. Text in, vectors out. **Must support batched embedding during ingestion** — never embed one chunk at a time in a loop. Default batch size = 32, tunable via config.
- **`vector_store.py`** — wraps ChromaDB. Owns ingest and query. No LLM logic here.
- **`pdf_loader.py`, `chunker.py`** — pure functions. Input in, output out, no side effects.
- **`agents/*.py`** — orchestrate tools to answer a query. One agent per file. Agents never import from each other.
- **`prompts/*.txt`** — versioned system prompts loaded at runtime. Behavior enforced by these prompts is specified in *Prompt Requirements* below.

## Prompt Requirements
The QA Expert agent's system prompt (`prompts/qa_expert.txt`) must enforce the following behaviors. These are non-negotiable and are validated by the golden test suite.

- **Cite retrieved chunks.** Every factual claim in the answer should reference the ISTQB section or chunk it came from.
- **Prefer ISTQB terminology.** Use canonical ISTQB vocabulary when a term exists (e.g. "equivalence partitioning" not "input grouping"; "test oracle" not "expected result source").
- **No speculation outside retrieved context.** If retrieved chunks do not cover the question, the agent must say so explicitly rather than filling the gap from pretraining.
- **Explicit uncertainty.** When a question is only partially covered, the answer must say "the retrieved context does not fully cover this" instead of hedging with weasel words.
- **Senior QA voice.** Responses read as a 15-year Senior QA Engineer mentoring a junior — not a textbook paraphrase.
- **Five-part concept contract.** For concept questions, answers include: (1) definition, (2) real project example, (3) suggested test cases, (4) common mistakes, (5) interview-style explanation.

## Error Handling
- **mimik unreachable** — raise a specific `MimikUnavailableError` from `llm_client.py`. CLI catches it and prints a friendly message telling the user to start the runtime. Do not retry indefinitely.
- **Empty retrieval** — if vector search returns no chunks, the agent must explicitly respond "I don't have enough information from the available documents to answer this." rather than letting the LLM hallucinate an answer.
- **PDF parse failure** — fail loudly during ingest. Never index a partially-parsed PDF silently.
- **LLM timeout** — one retry with backoff, then fail. 30-second hard timeout per request.
- Always log errors via `logging` at the appropriate level. Never use bare `except:` to swallow exceptions.

## Coding Standards
- Type hints on every function signature.
- Google-style docstrings on every public function.
- No `print()` outside `cli.py` — use `logging` everywhere else.
- Functions under ~40 lines. Split if longer.
- One agent = one module. Agents do not cross-import.
- No hidden state in tools. Pure functions preferred.
- Constants live in `config.py` or `.env`, never inline in source — except for diagnostic guardrails internal to a single module (e.g., warning thresholds), which may be module-level constants.

## Observability
Log at each pipeline stage using Python's `logging` module. Use **structured key=value format** so logs can be grepped and parsed.

- `INFO` — pipeline milestones.
- `DEBUG` — per-chunk or per-request detail.
- `ERROR` — exceptions. Always include context.

Minimum INFO events during **ingestion**:
```
INFO ingestion_started     path=<pdf_path>
INFO chunks_generated      count=<N> chunk_size=500 overlap=100
INFO embeddings_created    count=<N> batch_size=32 duration_s=<t>
INFO vector_store_updated  collection=<n> count=<N>
INFO ingestion_completed   duration_s=<t>
```

Minimum INFO events during **query**:
```
INFO query_received        length_chars=<n>
INFO retrieved             top_k=<n> scores=[<s1>, <s2>, ..., <sn>]
INFO llm_called            model=<n> words_in=<n>
INFO answer_returned       duration_s=<t>
```

Do not log PDF content or full answers at INFO level — use DEBUG. Never log `.env` values.

## Testing Strategy
- **Unit tests** for every module in `qa_agent/`. A module is not considered complete without tests.
- **Mock the mimik endpoint** in unit tests — do not hit real mimik in standard test runs.
- **Integration tests** hit real mimik, live in `tests/integration/`, and are skipped by default (`@pytest.mark.integration`).
- **RAG quality suite** — a golden set of ≥10 ISTQB Q&A pairs lives in `tests/golden/`. This is an evaluation harness, not a pass/fail gate. Results are documented honestly — failures are evidence of model limitations, not blockers.
- **Golden test scoring** — each golden Q&A is evaluated on three dimensions:
  1. **Concept correctness** — the answer accurately describes the ISTQB concept being asked about.
  2. **Terminology coverage** — the answer uses correct canonical ISTQB vocabulary.
  3. **Hallucination absence** — every factual claim in the answer traces to a retrieved chunk, or is explicitly flagged as uncertain.
- Test naming: `test_<module>_<behavior>_<expected>`, e.g. `test_chunker_long_text_splits_with_overlap`.

## Workflow Rules
- Branch from `main`. Branch names: `feat/<short-desc>`, `fix/<short-desc>`, `chore/<short-desc>`, `docs/<short-desc>`.
- Conventional commit messages: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`.
- One logical change per PR. Do not mix refactor with new feature.
- PR description includes: what changed, why, how it was tested.
- `main` is branch-protected. All changes go through a PR, even when solo.
- Never commit to `main` directly.
- One step per commit where possible. Commit messages name the step: `feat(step-3): add ping CLI subcommand`.

## Quality Gate
A step, feature, or phase is **done** only when all of these are true:

- Tests pass locally (`poetry run pytest`).
- Lint is clean (`poetry run ruff check .`).
- Format is clean (`poetry run ruff format --check .`).
- Every new public function has a docstring and type hints.
- README reflects any user-facing change.
- The step's exit test has been run by the user and produced the expected output.
- For phase transitions: the phase's exit criterion is met (see roadmap below).

**Project exit criterion:** Step 10 golden test harness implemented and executed. Results documented in TODO.md or RESULTS.md — pass rate is informative, not gating. Project is complete when the harness works and results are published.

## Security
- `.env` is gitignored. `.env.example` is committed with keys but no values.
- ISTQB PDFs are never committed. `data/istqb_docs/` is gitignored.
- `chroma_db/` is never committed.
- No cloud API keys anywhere in the repo. No cloud LLM calls, ever.
- No real user PII in test data. Use synthetic QA questions only.

## When Unsure
- **Prefer smaller scope.** When a task is ambiguous, pick the minimum viable interpretation and surface the ambiguity back to the user.
- **Do not guess on the stack.** If a library seems missing, ask before adding — the stack is intentionally small.
- **Do not invent new agents or layers.** The current phase and step define what exists. If it is not in the current step, it does not belong.
- **Prefer asking over assuming.** One clarifying question is cheaper than an hour of wrong work.
- **When in doubt about whether to generate the next file, do not generate it.** Ask the user.

## What This Project Is NOT
- **Not production software.** No SLAs, no availability targets, no multi-user concerns.
- **Not a LangChain or LlamaIndex wrapper.** The point is to build RAG from primitives in order to learn how it works.
- **Not a cloud-hosted service.** Local-only is a hard constraint.
- **Not a multi-agent system.** One agent. Additional agents are future possibilities, not planned work.
- **Not a general-purpose QA tool.** Scoped strictly to ISTQB mentor behavior.
- **Not a chatbot with memory.** Stateless Q&A in Phase 1; conversation memory is a later, explicit decision.

## Non-Goals
The following are out of scope for this project. See "Future Possibilities" at the end of this file for things that could be revisited in a follow-on project.

- Conversation memory / multi-turn chat
- Multi-agent orchestration
- Web or HTTP interface
- Streaming LLM responses
- LLM tool-calling / function-calling
- Autonomous planning or ReAct-style reasoning loops
- Re-ranking over top-k results
- Hybrid search (dense + sparse / BM25)
- PDF ingestion UI or file upload

---

## Project Roadmap

**Phase 1 (current and final):** Single-agent RAG. Ingest → chunk → embed → ChromaDB → CLI Q&A with grounded answers, abstain logic, and citation enforcement. Step 10 (golden evaluation suite) is the final deliverable.

## Phase 1 Step Map
Phase 1 is executed as ten primary steps plus one mid-course addition (Step 8b). Each step is one Claude Code session, one deliverable, one review checkpoint. Do not start step N+1 until step N's exit test has been run and confirmed by the user.

| # | Deliverable | Exit test |
|---|---|---|
| 1 | `pyproject.toml`, `.env.example`, `.gitignore`, `qa_agent/__init__.py` | `poetry install` succeeds |
| 2 | `config.py` + `tests/unit/test_config.py` | `pytest tests/unit/test_config.py` passes |
| 3 | `llm_client.py`, `cli.py` (ping only), `tests/unit/test_llm_client.py` (mocked) | `qa-agent ping` returns "pong" against real mimik |
| 4 | `pdf_loader.py` + `tests/unit/test_pdf_loader.py` | test passes on a sample PDF |
| 5 | `chunker.py` + `tests/unit/test_chunker.py` | test verifies chunk size and overlap |
| 6 | `embeddings.py` + `tests/unit/test_embeddings.py` | test verifies batching and vector dimensions |
| 7 | `vector_store.py` + `tests/unit/test_vector_store.py` | test verifies ingest + query round-trip |
| 8 | `ingest` subcommand in `cli.py` + `tests/integration/test_ingest.py` | `qa-agent ingest <pdf>` runs end-to-end with full INFO logs |
| 8b | Provenance metadata (`source_doc`, `page`, `chunk_index`, `chunk_id`) in chunks and ChromaDB | all 44 tests pass; `qa-agent ingest` stores metadata per chunk |
| 9 | `agents/qa_expert.py`, `prompts/qa_expert.txt`, `ask` subcommand | `qa-agent ask "<question>"` returns a grounded answer |
| 10 | `tests/golden/test_rag_quality.py` with ≥10 Q&A pairs | harness runs end-to-end; results documented. **Project complete.** |

### Step 9 design decisions

Citation format:
- LLM output uses inline `[page N]` markers for specific claims.
- Answer ends with a References block listing source_doc, page, and chunk_id for each cited chunk.

Context block format (built by `qa_expert.answer`, passed in user message):

```
[1] Source: <source_doc> | Page <page> | chunk_id: <id>
<chunk text>

[2] Source: <source_doc> | Page <page> | chunk_id: <id>
<chunk text>

...

Question: <user question>
```

System prompt = persona + output format instructions from `qa_agent/prompts/qa_expert.txt` (static, never varies per query).
User message = numbered context blocks + question (dynamic per-call).

Abstain behavior:
- If hits is empty, return fixed message: "I don't have enough information from the available documents to answer this."
- If `hits[0]["score"] < settings.abstain_threshold`, return same fixed message. Default threshold: 0.35.
- In both abstain cases, do NOT call the LLM.

Logging events emitted from `qa_expert.answer()`:
```
INFO  query_received    length_chars=<n>
INFO  retrieved         top_k=<n> scores=[<s1>, <s2>, ...]
DEBUG retrieved_chunk   rank=<i> score=<s> source_doc=<d> page=<p> chunk_id=<id>
INFO  answer_returned   duration_s=<t>
```
(One `retrieved_chunk` DEBUG line per chunk; visible only at DEBUG log level.)

Prompt size safeguard:
- After the user message is built (numbered context blocks + question) but before calling `llm_client.chat()`, check the word count of the combined system prompt + user message.
- If word count > 1500, emit `WARNING prompt_words=<n> exceeds_threshold=True` and proceed with the call anyway. The warning is diagnostic, not blocking — smollm2 may still produce a useful answer; we just want the size visible.
- Threshold (1500) is a module-level constant in `qa_expert.py`: `_PROMPT_WORD_WARN_THRESHOLD = 1500`. Not in config — this is a diagnostic guardrail for development, not a runtime parameter.

`cli.py` `_cmd_ask` is a thin adapter: emits no logging itself. Catches `MimikUnavailableError`, prints to stderr, exits 1 — same pattern as `_cmd_ping`.

Unit test scope for Step 9 (`tests/unit/test_qa_expert.py`):
- `test_answer_returns_abstain_when_top_score_below_threshold`
- `test_answer_returns_no_context_when_retrieval_empty`
- `test_answer_calls_llm_when_top_score_above_threshold`
- `test_answer_propagates_mimik_unavailable`

All four tests use mocked `vector_store.query` and `llm_client.chat`. Behavioral quality of real answers is evaluated by the Step 10 golden suite, not Step 9 unit tests.

## Known Limitations

These are documented facts about the current system, not bugs to fix before shipping.

- **Model too small for reliable structured output.** `smollm2-360m` (360M params) cannot reliably follow the five-part format contract or inline citation rules. Step 9 smoke test confirmed the model produced incorrect content (described continuous performance testing instead of metamorphic testing) even when the correct chunk was retrieved.
- **Context window constraint.** smollm2-360m has ~2K token context. Four 500-word chunks plus system prompt plus question exceeded this limit, causing `llama_decode()` failure. `top_k` is temporarily reduced to 2 as a workaround.
- **Word-based chunking.** `chunker.py` splits on words, not tokens. `chunk_size=500` produces chunks of inconsistent token length. A token-accurate chunker would require `tiktoken` or similar.
- **Step 10 golden results will reflect model limitations.** This is intentional — the golden suite is an honest evaluation, not a quality gate. Results are published as evidence.

## Future Possibilities

These are design ideas preserved from the original roadmap. None are planned; all would require a new project or a deliberate Phase 2 decision.

- **Test Case Generator agent** — given a feature description, generate BVA, equivalence partitioning, decision table, and pairwise test cases.
- **Interview Coach agent** — generates ISTQB interview questions, scores answers, suggests improvements.
- **FastAPI service** — wrap agents behind an HTTP API with a minimal web UI.
- **Model upgrade** — replace `smollm2-360m` with `Qwen2.5-3B-Instruct` or similar 3B+ model via mimOE. Would unlock reliable structured output, restore `top_k=4`, and meaningfully improve golden suite scores.