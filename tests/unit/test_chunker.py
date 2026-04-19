"""Unit tests for qa_agent.chunker.chunk_texts.

Tests exercise the module's current word-based splitting behaviour.
The known words-vs-tokens discrepancy with CLAUDE.md Retrieval Strategy
is tracked in TODO.md and is out of scope here.
"""
import pytest

from qa_agent.chunker import chunk_texts


def test_chunker_chunk_size_not_exceeded() -> None:
    """Every chunk contains at most chunk_size words."""
    words = [f"word{i}" for i in range(25)]
    pages = [" ".join(words)]

    result = chunk_texts(pages, chunk_size=6, chunk_overlap=2)

    assert result, "expected at least one chunk"
    for chunk in result:
        assert len(chunk.split()) <= 6


def test_chunker_overlap_shared_between_consecutive_chunks() -> None:
    """Consecutive full-size chunks share exactly chunk_overlap words."""
    # 6 words, chunk_size=4, overlap=2, stride=2 → produces two full chunks
    # chunk 0: w0 w1 w2 w3   chunk 1: w2 w3 w4 w5
    words = [f"w{i}" for i in range(6)]
    pages = [" ".join(words)]

    result = chunk_texts(pages, chunk_size=4, chunk_overlap=2)

    assert len(result) >= 2
    first_words = result[0].split()
    second_words = result[1].split()
    # Last overlap words of chunk 0 must equal first overlap words of chunk 1
    assert first_words[-2:] == second_words[:2]


def test_chunker_empty_input_returns_empty_list() -> None:
    """An empty pages list and pages containing only whitespace both return []."""
    assert chunk_texts([], chunk_size=500, chunk_overlap=100) == []
    assert chunk_texts(["", "   "], chunk_size=500, chunk_overlap=100) == []


def test_chunker_text_shorter_than_chunk_size_produces_single_chunk() -> None:
    """Text with fewer words than chunk_size is returned as one chunk."""
    pages = ["alpha beta gamma delta"]  # 4 words, chunk_size=10

    result = chunk_texts(pages, chunk_size=10, chunk_overlap=2)

    assert len(result) == 1
    assert result[0] == "alpha beta gamma delta"


def test_chunker_word_order_preserved_across_chunks() -> None:
    """Words appear in their original order when traversing all chunks in sequence."""
    words = [f"token{i:02d}" for i in range(14)]
    pages = [" ".join(words)]

    result = chunk_texts(pages, chunk_size=5, chunk_overlap=2)

    # Collect unique words in first-seen order across all chunks
    seen: list[str] = []
    for chunk in result:
        for word in chunk.split():
            if word not in seen:
                seen.append(word)

    assert seen == words


def test_chunker_multiple_pages_are_concatenated() -> None:
    """Words from all pages are joined into one flat stream before chunking."""
    pages = ["alpha beta gamma", "delta epsilon zeta"]

    result = chunk_texts(pages, chunk_size=10, chunk_overlap=1)

    assert len(result) == 1
    chunk_words = result[0].split()
    assert chunk_words == ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]


def test_chunker_raises_value_error_when_overlap_equals_chunk_size() -> None:
    """chunk_overlap == chunk_size must raise ValueError (stride would be zero)."""
    with pytest.raises(ValueError):
        chunk_texts(["some text here"], chunk_size=5, chunk_overlap=5)


def test_chunker_raises_value_error_when_overlap_exceeds_chunk_size() -> None:
    """chunk_overlap > chunk_size must raise ValueError."""
    with pytest.raises(ValueError):
        chunk_texts(["some text here"], chunk_size=5, chunk_overlap=6)
