# TODO

Known gaps flagged during audit. Fix these before Phase 1 exit criteria are evaluated.

- [ ] `chunker.py` uses words as the unit of measurement. CLAUDE.md Retrieval Strategy specifies tokens (chunk_size=500 tokens). The two are not equivalent — a word-based split will produce chunks of inconsistent token length.
- [ ] `llm_client.py` logs `tokens_in=<word_count>` but the value is a word count, not a real token count. The label is misleading for anyone reading the logs.
- [ ] `vector_store.py` hardcodes `{"hnsw:space": "cosine"}` directly in the collection creation call. CLAUDE.md says all retrieval parameters must live in `config.py` and be overridable via `.env`.
- [ ] `config.py` field `embed_batch_size` must be verified against the key name used in `.env.example` when that file is created — confirm the env var is `EMBED_BATCH_SIZE` and matches pydantic-settings' automatic name resolution.
