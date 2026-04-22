from __future__ import annotations

import logging
import uuid

import chromadb

from qa_agent.config import settings
from qa_agent.embeddings import embed_texts

logger = logging.getLogger(__name__)

_client: chromadb.PersistentClient | None = None


def _get_collection() -> chromadb.Collection:
    """Return (or create) the persistent ChromaDB collection."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_path)
    return _client.get_or_create_collection(
        name=settings.chroma_collection,
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(chunks: list[str]) -> None:
    """Embed and store a list of text chunks in the vector store.

    Args:
        chunks: Text chunks to index.
    """
    if not chunks:
        logger.debug("vector_store_add_skipped reason=empty_chunks")
        return

    collection = _get_collection()
    vectors = embed_texts(chunks)
    ids = [str(uuid.uuid4()) for _ in chunks]

    collection.add(documents=chunks, embeddings=vectors, ids=ids)

    logger.info(
        f"vector_store_updated collection={settings.chroma_collection} "
        f"count={len(chunks)}"
    )


def reset_collection() -> None:
    """Delete the collection and clear the cached client so the next
    call to _get_collection recreates both fresh.
    """
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_path)
    try:
        _client.delete_collection(settings.chroma_collection)
    except Exception:  # noqa: BLE001
        # Collection may not exist yet; that's fine.
        pass
    _client = None
    logger.info(f"collection_reset name={settings.chroma_collection}")


def query(question: str, top_k: int | None = None) -> list[dict]:
    """Retrieve the most relevant chunks for a question.

    Args:
        question: The user's question string.
        top_k: Number of results to return; defaults to config value.

    Returns:
        List of dicts with keys ``text`` and ``score``.
    """
    k = top_k or settings.top_k
    collection = _get_collection()
    question_vec = embed_texts([question])[0]

    results = collection.query(
        query_embeddings=[question_vec],
        n_results=k,
        include=["documents", "distances"],
    )

    docs = results["documents"][0] if results["documents"] else []
    distances = results["distances"][0] if results["distances"] else []

    # ChromaDB cosine distance: similarity = 1 - distance
    hits = [
        {"text": doc, "score": round(1.0 - dist, 4)}
        for doc, dist in zip(docs, distances)
    ]

    scores = [h["score"] for h in hits]
    logger.info(f"retrieved top_k={k} scores={scores}")
    return hits


def collection_count() -> int:
    """Return the number of documents in the collection."""
    return _get_collection().count()