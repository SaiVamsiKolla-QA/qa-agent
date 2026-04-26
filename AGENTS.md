# QA Expert Agent

A local RAG-based ISTQB mentor that answers software testing questions grounded in retrieved ISTQB documentation, running entirely on [mimik AI Foundation](https://mimik.com).

Built from primitives (no LangChain, no LlamaIndex) as a learning project in Python, embeddings, and RAG mechanics. Phase 1 is complete. The system runs on `smollm2-360m` (360M params), which is too small for reliable structured output — answers work, but don't consistently follow the five-part format. RESULTS.md documents the 3/10 baseline. See Known Limitations.

**What's working:** `qa-agent ingest` (PDF → ChromaDB), `qa-agent ask` (question → grounded answer with abstain logic and citations), 52 passing tests, golden evaluation harness with published results.  
**Not implemented:** No web interface, no multi-turn memory, no second agent.

---

## Quick start

Requires Python 3.13, Poetry 2.x, and [mimik AI Foundation](https://mimik.com) installed locally.

```bash
git clone https://github.com/SaiVamsiKolla-QA/qa-agent.git
cd qa-expert-agent
poetry install
cp .env.example .env
```

Edit `.env` and confirm `MODEL_NAME` matches the model your mimOE runtime serves.

```bash
mimoe start                                          # start mimOE if not running
poetry run qa-agent ping                             # should print: mimik reachable. model reply: ...
poetry run qa-agent ingest data/istqb_docs/<file>.pdf
poetry run qa-agent ask "What is metamorphic testing?"
```

mimOE must be running on `localhost:8083` with `smollm2-360m` (or a substitute model configured in `.env`).

---

## Architecture at a glance

```
qa_agent/
  cli.py                — CLI subcommands: ping, ingest, ask
  pdf_loader.py         — PDF text extraction with per-page metadata
  chunker.py            — word-based chunking with configurable overlap
  embeddings.py         — sentence-transformers batch embedding wrapper
  vector_store.py       — ChromaDB storage, retrieval, and reset
  llm_client.py         — mimik AI Foundation HTTP client (OpenAI-compatible)
  agents/
    qa_expert.py        — answer(): retrieval → abstain check → prompt → LLM
  prompts/
    qa_expert.txt       — system prompt: persona, five-part format, citation rules
  config.py             — pydantic-settings runtime config (loaded from .env)
```

**Ingestion pipeline:**
```
PDF → pdf_loader (pages + page numbers)
    → chunker (word-based, with source_doc/page/chunk_id metadata)
    → embeddings (batched, all-MiniLM-L6-v2)
    → vector_store.add_chunks() → ChromaDB (replaces collection each run)
```

**Query pipeline:**
```
question → embed (all-MiniLM-L6-v2)
         → ChromaDB cosine query → top-k hits with scores
         → abstain if empty or top score < 0.35
         → numbered context blocks ([1] Source | Page | chunk_id + text)
         → llm_client.chat(system_prompt, user_message)
         → smollm2-360m via mimOE → answer with inline [page N] citations
```

All retrieval parameters (`top_k`, `abstain_threshold`, `chunk_size`, `hnsw_space`) live in `config.py` and are overridable via `.env`.

---

## How to run things

### Run tests

```bash
poetry run pytest                   # 52 tests (unit + integration; no mimOE needed)
poetry run pytest tests/golden/ -v  # golden evaluation suite (needs mimOE running)
```

### Ingest a document

```bash
poetry run qa-agent ingest data/istqb_docs/CT-AI-Syllabus.pdf
```

Each ingest call replaces the ChromaDB collection — idempotent, safe to re-run.

### Ask a question

```bash
poetry run qa-agent ask "What is metamorphic testing?"
poetry run qa-agent ask "How does ISTQB define a test oracle?"
```

The agent returns the abstain message ("I don't have enough information from the available documents to answer this.") if no chunk scores above 0.35.

### Prompt size diagnostic

```bash
poetry run python scripts/token_count.py "some text here"
echo "some text" | poetry run python scripts/token_count.py
```

Uses tiktoken if installed; falls back to word count. Useful for checking whether a prompt will fit smollm2's ~2K context window.

---

## Code conventions

- **Python 3.13, Poetry** for dependency management.
- **All runtime config** lives in `qa_agent/config.py` and is loaded from `.env` via pydantic-settings. No magic numbers inline in source — with one exception: diagnostic guardrails (e.g., the 1500-word prompt-size warning threshold) may be module-level constants when they are internal to a single module.
- **Logging** is structured `key=value` format. `INFO` for pipeline milestones; `DEBUG` for per-chunk detail. Third-party loggers (httpx, transformers, chromadb) are silenced to `WARNING` in `_configure_logging()` in `cli.py`.
- **`print()` only in `cli.py`** — all other modules use `logging`.
- **Tests** follow Arrange-Act-Assert. Mocks target the import location in the module under test (e.g., `qa_agent.agents.qa_expert.vector_store.query`), not the definition site. Unit tests mock all I/O; integration tests hit real mimOE and are skipped by default via `@pytest.mark.integration`.
- **No orchestration frameworks.** ChromaDB and the OpenAI Python SDK (pointed at localhost) are the only AI-adjacent libraries. This is intentional — the project exists to learn RAG mechanics, not wrap them.
- **Commit style:** conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`). One logical change per commit.

---

## Known limitations

- **Model too small for reliable structured output.** `smollm2-360m` (360M params) does not consistently follow the five-part answer format or inline citation rules. The Step 10 golden suite will document specific failure modes as a baseline. Future fix: upgrade to `Qwen2.5-3B-Instruct` or equivalent via mimOE.
- **`top_k` temporarily set to 2.** smollm2-360m's ~2K token context cannot fit four 500-word chunks plus the system prompt plus the question. Context overflow caused `llama_decode()` failures in early smoke tests. Restore to 4+ after model upgrade.
- **Word-based chunking, not token-based.** `chunker.py` splits on words. `chunk_size=500` produces chunks of inconsistent token length. A token-accurate chunker (using `tiktoken`) would be more precise but is not implemented.
- **Page citations are start-of-chunk only.** Chunks that span a page boundary cite the page where the chunk begins, not where a specific claim appears.
- **HF Hub auth warning on every embedding load.** `sentence_transformers` writes an "unauthenticated request" warning directly to stderr, bypassing Python's logging system. Two suppression attempts failed. Accepted as cosmetic noise.

---

## Where to look first

| If you want to understand… | Read… |
|---|---|
| Design decisions and the "why" | `CLAUDE.md` — authoritative spec |
| Open issues and future work | `TODO.md` |
| How each module behaves | `tests/unit/` — concrete examples |
| The agent's persona and output format | `qa_agent/prompts/qa_expert.txt` |
| Retrieval and config parameters | `qa_agent/config.py` |

**Before making significant changes:** read `CLAUDE.md` in full. It defines layer responsibilities, observability conventions, forbidden tools, and the rationale behind key decisions.

**Before committing:** run `poetry run pytest` and `poetry run ruff check .` to verify nothing is broken.
