"""Unit tests for qa_agent.embeddings.embed_texts.

Uses the real all-MiniLM-L6-v2 model — no mocking.
First run downloads ~80 MB and caches in ~/.cache/huggingface/hub/.
Subsequent runs are fully offline.
"""

import math

from qa_agent.embeddings import embed_texts

# all-MiniLM-L6-v2 produces 384-dimensional vectors.
# If this constant changes, the model was swapped and downstream
# ChromaDB collections will be incompatible — failing here is correct.
_EXPECTED_DIM = 384


def _cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two equal-length vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b)


def test_embeddings_returns_one_vector_per_text() -> None:
    """embed_texts returns exactly one vector per input string."""
    texts = ["first sentence", "second sentence", "third sentence"]

    result = embed_texts(texts)

    assert len(result) == len(texts)


def test_embeddings_vector_dimension_is_384() -> None:
    """Each vector has the 384 dimensions expected from all-MiniLM-L6-v2."""
    result = embed_texts(["any text will do"])

    assert len(result[0]) == _EXPECTED_DIM


def test_embeddings_same_text_produces_identical_vectors() -> None:
    """embed_texts is deterministic: the same input always yields the same vector."""
    text = ["deterministic input sentence"]

    first = embed_texts(text)[0]
    second = embed_texts(text)[0]

    assert first == second


def test_embeddings_similar_texts_score_higher_than_unrelated() -> None:
    """Semantically similar texts have higher cosine similarity than unrelated ones."""
    anchor = embed_texts(["The cat sat on the mat"])[0]
    similar = embed_texts(["The dog sat on the mat"])[0]
    unrelated = embed_texts(["Quantum mechanics describes subatomic particles"])[0]

    assert _cosine(anchor, similar) > _cosine(anchor, unrelated)


def test_embeddings_batch_larger_than_batch_size_preserves_count_and_order() -> None:
    """Batching across multiple internal batches returns vectors in input order."""
    texts = [f"sentence number {i}" for i in range(5)]

    # batch_size=2 forces three batches internally for 5 texts
    batched = embed_texts(texts, batch_size=2)
    individual = [embed_texts([t])[0] for t in texts]

    assert len(batched) == len(texts)
    for i, (b, ind) in enumerate(zip(batched, individual)):
        # Cosine similarity of 1.0 (within float precision) confirms same vector
        assert _cosine(b, ind) > 0.9999, (
            f"vector at position {i} differs between batched and individual encoding"
        )


def test_embeddings_empty_list_returns_empty_list() -> None:
    """embed_texts([]) returns [] without loading the model or raising."""
    result = embed_texts([])

    assert result == []
