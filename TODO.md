# TODO

Known gaps flagged during audit. Fix these before Phase 1 exit criteria are evaluated.

- [ ] `chunker.py` uses words as the unit of measurement. CLAUDE.md Retrieval Strategy specifies tokens (chunk_size=500 tokens). The two are not equivalent — a word-based split will produce chunks of inconsistent token length.
- [ ] `llm_client.py` logs `tokens_in=<word_count>` but the value is a word count, not a real token count. The label is misleading for anyone reading the logs.
- [x] `llm_client.py` hardcoded `api_key="not-used"` (fixed: moved to `settings.mimik_api_key`)
- [x] `MODEL_NAME` placeholder in `.env` (fixed: set to `smollm2-360m`)
- [ ] `vector_store.py` hardcodes `{"hnsw:space": "cosine"}` directly in the collection creation call. CLAUDE.md says all retrieval parameters must live in `config.py` and be overridable via `.env`.
- [ ] `config.py` field `embed_batch_size` must be verified against the key name used in `.env.example` when that file is created — confirm the env var is `EMBED_BATCH_SIZE` and matches pydantic-settings' automatic name resolution.

## Post-Step-3
- [ ] `smollm2-360m` (360M params) is too small for serious ISTQB Q&A.
      Before Phase 1 Step 10 (golden suite), switch to a 3B or 7B
      instruct model. Update `MODEL_NAME` in `.env` accordingly.
- [x] CLAUDE.md references env var `MIMIK_BASE_URL` in at least one
      place but the code uses `MIMIK_ENDPOINT`. Reconcile naming so
      CLAUDE.md matches `config.py`. (resolved: CLAUDE.md no longer
      references BASE_URL; config.py uses `mimik_endpoint`)

## Troubleshooting notes (from Step 2 recovery)
- If `poetry run pytest` reports pytest 8.x or Python 3.10, the Homebrew pytest
  on PATH is shadowing the venv pytest. Verify with `which pytest` — if it
  points outside `.venv/`, invoke `.venv/bin/pytest` directly or check that
  `poetry install --with dev` actually populated the venv.
- If `$VIRTUAL_ENV` is set to a non-venv path (e.g. a base Python framework),
  VS Code's Python extension has activated a stale interpreter. Fix: reopen
  the project folder in VS Code and select `.venv/bin/python` as interpreter.
- `pyproject.toml` uses Poetry-native `[tool.poetry.group.dev.dependencies]`
  syntax, not PEP 735 `[dependency-groups]`. Do not switch — Poetry 2.1.x does
  not install PEP 735 dev groups with `poetry install`.
- Always run `poetry check` before `poetry lock` after editing pyproject.toml.
  It validates TOML grammar without any side effects.

  ### Troubleshooting

**`poetry run` fails with `ModuleNotFoundError` even though `poetry install` succeeded.**
This is caused by VS Code's Python extension injecting `VIRTUAL_ENV` pointing at a system Python installation rather than the project's `.venv`. The repo includes `.vscode/settings.json` with `python.defaultInterpreterPath` set to `${workspaceFolder}/.venv/bin/python` to prevent this. If the issue still occurs after cloning:

1. Open the project folder directly in VS Code (not a parent folder).
2. Reload the window: `Cmd+Shift+P` → `Developer: Reload Window`.
3. Select the correct interpreter manually: `Cmd+Shift+P` → `Python: Select Interpreter` → choose `./.venv/bin/python`.
4. Open a new integrated terminal and verify: `echo $VIRTUAL_ENV` should print the path ending in `.venv`.
5. As a fallback, invoke the venv directly instead of through Poetry: `.venv/bin/qa-agent ping` and `.venv/bin/pytest`.

**`poetry run qa-agent ping` returns "mimik not reachable".**
mimik AI Foundation does not auto-start. Check status with `mimoe status` and start with `mimoe start`.

**`mimik reachable. model reply:` is followed by strange text.**
The default model (`smollm2-360m`) is a small 360M-parameter model chosen for fast local development. Its answers are often rambling or off-topic. For serious ISTQB Q&A quality, switch to a 3B or 7B instruct model by updating `MODEL_NAME` in `.env`.
## Post-Step-7
- [x] Fixed: vector_store.py line 11 had `chromadb.PersistentClient | None`
      as a module-level annotation that evaluated at import time.
      ChromaDB 1.5.x exports PersistentClient as a factory function,
      not a class, so the `|` union raised TypeError. Fix: added
      `from __future__ import annotations` to defer annotation
      evaluation. Surfaced by Step 7 tests. (Commit: fix(vector_store)...)

## Post-Step-8
- [x] Logging verbosity: `logging.basicConfig(level=INFO)`
      in cli.py turns on INFO for all libraries, producing
      ~30 lines of httpx / transformers / pypdf noise during
      ingestion. Silence third-party loggers by setting
      `logging.getLogger("httpx").setLevel(WARNING)` and
      similar for urllib3, transformers, pypdf. Keep
      qa_agent's own loggers at INFO. (fixed: extracted
      `_configure_logging()` in cli.py that silences noisy
      third-party loggers after basicConfig)
- [x] `chroma_db/` now contains a persistent ChromaDB
      collection with 88 chunks from the Step 8 manual
      smoke test. Running `ingest` again will accumulate
      more chunks rather than replace them. Decide before
      Step 10: should `ingest` replace the collection each
      time, or append? Default behaviour today is append.
      (fixed: ingest now replaces — `reset_collection()` added
      to vector_store.py; called in `_cmd_ingest` before
      `add_chunks`)

## Pre-Step-9 (from Codex review)
Four safeguards to fold into Step 9's ask flow:
- [ ] Retrieval diagnostics logging — one INFO line per retrieved
      chunk with score, source_doc, page
- [ ] Citation-constrained prompt — LLM must emit structured output
      with chunk_id or page references, not just prose citations
- [ ] Abstain on weak evidence — if top similarity score < 0.35,
      return "I don't have enough information from the available
      documents" instead of calling the LLM
- [ ] Token count check — log total prompt tokens before LLM call,
      flag if > 1500 (smollm2 has ~2K context)

- [ ] Library output noise (partial fix attempted twice, reverted both times):
      sentence_transformers / huggingface_hub / transformers print
      directly to stderr (not via logging or warnings) on model load:
      "unauthenticated requests" warning, "Loading weights" progress
      bar, "BertModel LOAD REPORT" block. Tried HF_HUB_DISABLE_IMPLICIT_TOKEN
      (no effect), tried adding "huggingface_hub" to noisy-loggers list
      (no effect since it's not a logger call). Accepted for now.
      Future options: TRANSFORMERS_VERBOSITY=error env var, stderr
      redirect during model load, or wait for lazy-import to make this
      fire only in commands that actually embed.
      Second attempt: Set HF_HUB_DISABLE_IMPLICIT_TOKEN=1 via
      os.environ.setdefault at the top of _configure_logging, and added
      huggingface_hub to the noisy-loggers list. Smoke test showed the
      warning was still emitted — sentence_transformers writes this message
      directly to stderr (not via logging or warnings), so neither approach
      suppressed it. Fix reverted. Accepted as permanent cosmetic noise
      unless TRANSFORMERS_VERBOSITY=error or stderr-redirect are attempted.

## Step 10 scope note
Minimum 10 golden questions (up from 5), drawn from CT-AI syllabus
content since that's what's in the corpus. Classical ISTQB questions
(equivalence partitioning, boundary values, decision tables) need
CTFL syllabus ingested first — defer to Phase 2 unless adding it
is trivial.

