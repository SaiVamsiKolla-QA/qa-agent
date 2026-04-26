import logging
from unittest.mock import patch

import pytest

from qa_agent.agents import qa_expert
from qa_agent.agents.qa_expert import ABSTAIN_MESSAGE
from qa_agent.llm_client import MimikUnavailableError

_ABOVE_THRESHOLD_HIT = {
    "text": "Metamorphic testing verifies output relationships across test inputs.",
    "score": 0.62,
    "source_doc": "ct-ai-syllabus.pdf",
    "page": 12,
    "chunk_index": 0,
    "chunk_id": "abc123",
}

_BELOW_THRESHOLD_HIT = {
    "text": "Some unrelated content.",
    "score": 0.20,
    "source_doc": "ct-ai-syllabus.pdf",
    "page": 5,
    "chunk_index": 0,
    "chunk_id": "xyz789",
}


@pytest.fixture
def stub_prompts_dir(tmp_path, monkeypatch):
    """Stub prompts directory with a minimal qa_expert.txt."""
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "qa_expert.txt").write_text("You are a QA expert.")
    from qa_agent.config import settings

    monkeypatch.setattr(settings, "prompts_dir", prompts)
    return prompts


def test_answer_returns_abstain_when_top_score_below_threshold(stub_prompts_dir):
    """Below-threshold top score returns abstain message without calling LLM."""
    with (
        patch("qa_agent.agents.qa_expert.vector_store.query") as mock_query,
        patch("qa_agent.agents.qa_expert.llm_client.chat") as mock_chat,
    ):
        mock_query.return_value = [
            {**_BELOW_THRESHOLD_HIT, "score": 0.20},
            {**_BELOW_THRESHOLD_HIT, "score": 0.15},
        ]
        result = qa_expert.answer("What is metamorphic testing?")

    assert result == ABSTAIN_MESSAGE
    mock_chat.assert_not_called()


def test_answer_returns_abstain_when_retrieval_empty(stub_prompts_dir):
    """Empty retrieval returns abstain message without calling LLM."""
    with (
        patch("qa_agent.agents.qa_expert.vector_store.query") as mock_query,
        patch("qa_agent.agents.qa_expert.llm_client.chat") as mock_chat,
    ):
        mock_query.return_value = []
        result = qa_expert.answer("What is metamorphic testing?")

    assert result == ABSTAIN_MESSAGE
    mock_chat.assert_not_called()


def test_answer_calls_llm_when_top_score_equals_threshold(stub_prompts_dir):
    """Score exactly equal to threshold should NOT abstain (uses strict <)."""
    with (
        patch("qa_agent.agents.qa_expert.vector_store.query") as mock_query,
        patch("qa_agent.agents.qa_expert.llm_client.chat") as mock_chat,
    ):
        hit_at_threshold = {
            "text": "Some content.",
            "score": 0.35,
            "source_doc": "test.pdf",
            "page": 1,
            "chunk_index": 0,
            "chunk_id": "boundary123",
        }
        mock_query.return_value = [hit_at_threshold]
        mock_chat.return_value = "test answer"

        result = qa_expert.answer("What is metamorphic testing?")

    assert result == "test answer"
    mock_chat.assert_called_once()


def test_answer_calls_llm_when_top_score_above_threshold(stub_prompts_dir):
    """Above-threshold score calls LLM with correctly structured prompt args."""
    with (
        patch("qa_agent.agents.qa_expert.vector_store.query") as mock_query,
        patch("qa_agent.agents.qa_expert.llm_client.chat") as mock_chat,
    ):
        mock_query.return_value = [_ABOVE_THRESHOLD_HIT]
        mock_chat.return_value = "test answer"

        result = qa_expert.answer("What is metamorphic testing?")

    assert result == "test answer"
    mock_chat.assert_called_once()
    _system_prompt, user_message = mock_chat.call_args.args
    assert "[1] Source:" in user_message
    assert "Question:" in user_message


def test_answer_propagates_mimik_unavailable(stub_prompts_dir):
    """MimikUnavailableError raised by llm_client propagates out of answer()."""
    with (
        patch("qa_agent.agents.qa_expert.vector_store.query") as mock_query,
        patch("qa_agent.agents.qa_expert.llm_client.chat") as mock_chat,
    ):
        mock_query.return_value = [_ABOVE_THRESHOLD_HIT]
        mock_chat.side_effect = MimikUnavailableError("test failure")

        with pytest.raises(MimikUnavailableError):
            qa_expert.answer("What is metamorphic testing?")


def test_answer_emits_warning_when_prompt_exceeds_word_threshold(
    stub_prompts_dir, caplog
):
    """Prompt word count over 1500 emits a WARNING with prompt_words= and
    exceeds_threshold=True before the LLM call."""
    assert (stub_prompts_dir / "qa_expert.txt").exists()
    # stub system prompt is 5 words; need hit text large enough to push
    # combined total above 1500. 1500 words gives ~1519 combined.
    large_text = " ".join(["word"] * 1500)
    large_hit = {
        "text": large_text,
        "score": 0.62,
        "source_doc": "test.pdf",
        "page": 1,
        "chunk_index": 0,
        "chunk_id": "large123",
    }

    with (
        patch("qa_agent.agents.qa_expert.vector_store.query") as mock_query,
        patch("qa_agent.agents.qa_expert.llm_client.chat") as mock_chat,
    ):
        mock_query.return_value = [large_hit]
        mock_chat.return_value = "answer"

        with caplog.at_level(logging.WARNING, logger="qa_agent.agents.qa_expert"):
            qa_expert.answer("What is metamorphic testing?")

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and "prompt_words" in r.message
    ]
    assert len(warning_records) == 1, (
        f"Expected exactly one prompt_words warning, got {len(warning_records)}"
    )
    assert "exceeds_threshold=True" in warning_records[0].message


# ---------------------------------------------------------------------------
# _build_user_message — prompt assembly contract
# ---------------------------------------------------------------------------


def test_build_user_message_includes_required_metadata_fields_per_block():
    """Each context block must contain source_doc, page, chunk_id, and text,
    with 'Question:' at the end."""
    from qa_agent.agents.qa_expert import _build_user_message

    hits = [
        {
            "text": "First chunk content.",
            "score": 0.62,
            "source_doc": "ct-ai-syllabus.pdf",
            "page": 12,
            "chunk_index": 0,
            "chunk_id": "abc123",
        },
        {
            "text": "Second chunk content.",
            "score": 0.55,
            "source_doc": "ct-ai-syllabus.pdf",
            "page": 18,
            "chunk_index": 1,
            "chunk_id": "def456",
        },
    ]
    question = "What is metamorphic testing?"

    result = _build_user_message(hits, question)

    assert "[1]" in result
    assert "ct-ai-syllabus.pdf" in result
    assert "Page 12" in result
    assert "chunk_id: abc123" in result
    assert "First chunk content." in result

    assert "[2]" in result
    assert "Page 18" in result
    assert "chunk_id: def456" in result
    assert "Second chunk content." in result

    assert "Question: What is metamorphic testing?" in result


def test_build_user_message_preserves_hit_rank_order():
    """Hits in input order [0, 1, 2] produce numbered blocks [1], [2], [3]
    in the same positional order in the output string."""
    from qa_agent.agents.qa_expert import _build_user_message

    hits = [
        {
            "text": f"Content for chunk {i}.",
            "score": 0.6 - i * 0.05,
            "source_doc": "test.pdf",
            "page": i + 1,
            "chunk_index": i,
            "chunk_id": f"chunk{i}",
        }
        for i in range(3)
    ]

    result = _build_user_message(hits, "test question")

    pos_1 = result.find("[1]")
    pos_2 = result.find("[2]")
    pos_3 = result.find("[3]")

    assert pos_1 != -1
    assert pos_2 != -1
    assert pos_3 != -1
    assert pos_1 < pos_2 < pos_3

    block_1 = result[pos_1:pos_2]
    block_3 = result[pos_3:]
    assert "Content for chunk 0." in block_1
    assert "chunk_id: chunk0" in block_1
    assert "Content for chunk 2." in block_3
    assert "chunk_id: chunk2" in block_3


def test_answer_does_not_warn_when_prompt_below_threshold(
    stub_prompts_dir, caplog
):
    """Prompt below 1500 words must NOT emit a prompt_words WARNING."""
    assert (stub_prompts_dir / "qa_expert.txt").exists()
    small_hit = {
        "text": "A short chunk of content.",
        "score": 0.62,
        "source_doc": "test.pdf",
        "page": 1,
        "chunk_index": 0,
        "chunk_id": "small1",
    }

    with (
        patch("qa_agent.agents.qa_expert.vector_store.query") as mock_query,
        patch("qa_agent.agents.qa_expert.llm_client.chat") as mock_chat,
    ):
        mock_query.return_value = [small_hit]
        mock_chat.return_value = "answer"

        with caplog.at_level(logging.WARNING, logger="qa_agent.agents.qa_expert"):
            qa_expert.answer("What is metamorphic testing?")

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and "prompt_words" in r.message
    ]
    assert len(warning_records) == 0, (
        f"Expected no prompt_words warning, got {len(warning_records)}"
    )
