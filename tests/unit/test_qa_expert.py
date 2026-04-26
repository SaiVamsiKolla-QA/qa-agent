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
