from unittest.mock import MagicMock, patch

import pytest
from openai import APIConnectionError

from qa_agent.llm_client import MimikUnavailableError, chat


def test_chat_returns_reply_on_success() -> None:
    """chat() returns the assistant message content string on a normal response."""
    with patch("qa_agent.llm_client.OpenAI") as MockOpenAI:
        mock_client = MockOpenAI.return_value
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "pong"
        mock_client.chat.completions.create.return_value = mock_response

        result = chat("reply with pong", "ping")

    assert result == "pong"


def test_chat_raises_mimik_unavailable_on_connection_error() -> None:
    """chat() raises MimikUnavailableError when the OpenAI client cannot connect."""
    with patch("qa_agent.llm_client.OpenAI") as MockOpenAI:
        mock_client = MockOpenAI.return_value
        mock_client.chat.completions.create.side_effect = APIConnectionError(
            request=MagicMock()
        )

        with pytest.raises(MimikUnavailableError):
            chat("reply with pong", "ping")
