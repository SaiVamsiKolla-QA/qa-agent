"""Unit tests for qa_agent.vector_store — add_chunks, query, collection_count.

Uses real ChromaDB (tmp_path-backed) and real sentence-transformer embeddings.
No mocking. Each test gets an isolated database via the _reset_store fixture.

ChromaDB 1.5.8 returns [] (not an exception) when querying an empty collection,
so the empty-query test asserts [] rather than catching an exception.
"""
import pytest

import qa_agent.vector_store as _vs
from qa_agent.vector_store import add_chunks, collection_count, query


def _make_chunks(texts: list[str], source_doc: str = "test.pdf") -> list[dict]:
    """Create minimal chunk dicts for testing add_chunks."""
    return [
        {
            "text": t,
            "source_doc": source_doc,
            "page": 1,
            "chunk_index": i,
            "chunk_id": f"cid-{i:04d}",
        }
        for i, t in enumerate(texts)
    ]


@pytest.fixture(autouse=True)
def _reset_store(tmp_path, monkeypatch):
    """Redirect ChromaDB to tmp_path and reset the cached client before each test."""
    monkeypatch.setattr(_vs.settings, "chroma_path", str(tmp_path))
    monkeypatch.setattr(_vs, "_client", None)
    yield
    # Ensure the next test always starts with a dead client reference.
    monkeypatch.setattr(_vs, "_client", None)


# ---------------------------------------------------------------------------
# collection_count
# ---------------------------------------------------------------------------

def test_vector_store_empty_collection_count_is_zero() -> None:
    """A freshly created collection contains zero documents."""
    assert collection_count() == 0


def test_vector_store_count_reflects_added_chunks() -> None:
    """collection_count returns the exact number of chunks that were added."""
    chunks = _make_chunks(["alpha chunk", "beta chunk", "gamma chunk"])

    add_chunks(chunks)

    assert collection_count() == len(chunks)


# ---------------------------------------------------------------------------
# add_chunks
# ---------------------------------------------------------------------------

def test_vector_store_add_empty_list_is_no_op() -> None:
    """add_chunks([]) neither raises nor adds documents to the collection."""
    add_chunks([])

    assert collection_count() == 0


# ---------------------------------------------------------------------------
# query — result shape and count
# ---------------------------------------------------------------------------

def test_vector_store_query_empty_collection_returns_empty_list() -> None:
    """query() on an empty collection returns [] without raising."""
    result = query("what is software testing?")

    assert result == []


def test_vector_store_query_result_dicts_have_all_expected_keys() -> None:
    """Every result dict contains text, score, source_doc, page, chunk_index, chunk_id."""
    add_chunks(_make_chunks(["software testing validates application behaviour"]))

    results = query("testing", top_k=1)

    assert len(results) == 1
    assert set(results[0].keys()) == {
        "text", "score", "source_doc", "page", "chunk_index", "chunk_id"
    }


def test_vector_store_query_metadata_values_round_trip() -> None:
    """Metadata stored in add_chunks is returned unchanged by query."""
    add_chunks(_make_chunks(["software testing validates application behaviour"]))

    results = query("testing", top_k=1)

    assert results[0]["source_doc"] == "test.pdf"
    assert results[0]["page"] == 1
    assert results[0]["chunk_index"] == 0
    assert results[0]["chunk_id"] == "cid-0000"


def test_vector_store_query_top_k_limits_result_count() -> None:
    """top_k caps the number of returned results regardless of collection size."""
    chunks = _make_chunks([
        "equivalence partitioning divides inputs into classes",
        "boundary value analysis tests at partition edges",
        "decision table testing combines condition combinations",
        "state transition testing covers state-change sequences",
    ])
    add_chunks(chunks)

    results = query("test design technique", top_k=2)

    assert len(results) == 2


# ---------------------------------------------------------------------------
# query — semantic correctness
# ---------------------------------------------------------------------------

def test_vector_store_query_top_result_is_semantically_closest_chunk() -> None:
    """The highest-ranked result is the chunk most semantically similar to the query."""
    testing_chunk = (
        "Equivalence partitioning is a black-box test design technique "
        "that divides input data into valid and invalid equivalence classes"
    )
    cooking_chunk = (
        "Pasta is made by mixing durum wheat semolina flour with water "
        "to form a stiff dough that is then shaped and dried"
    )
    space_chunk = (
        "The Apollo 11 mission successfully landed astronauts on the lunar "
        "surface in July 1969, fulfilling the goal set by President Kennedy"
    )
    add_chunks(_make_chunks([testing_chunk, cooking_chunk, space_chunk]))

    results = query("black-box test design methods for software quality", top_k=3)

    assert results[0]["text"] == testing_chunk


def test_vector_store_query_scores_are_in_valid_cosine_range() -> None:
    """Returned similarity scores fall within [0.0, 1.0]."""
    add_chunks(_make_chunks(["software testing finds defects in applications under test"]))

    results = query("software defects", top_k=1)

    assert len(results) == 1
    score = results[0]["score"]
    assert 0.0 <= score <= 1.0
