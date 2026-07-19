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


def test_chat_omits_generation_params_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no overrides and None settings, the request carries no
    temperature, seed, or max_tokens keys (historical behavior)."""
    from qa_agent.config import settings

    monkeypatch.setattr(settings, "llm_temperature", None)
    monkeypatch.setattr(settings, "llm_seed", None)
    monkeypatch.setattr(settings, "llm_max_tokens", None)

    with patch("qa_agent.llm_client.OpenAI") as MockOpenAI:
        mock_client = MockOpenAI.return_value
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "pong"
        mock_client.chat.completions.create.return_value = mock_response

        chat("reply with pong", "ping")

    request_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert "temperature" not in request_kwargs
    assert "seed" not in request_kwargs
    assert "max_tokens" not in request_kwargs


def test_chat_passes_generation_params_when_provided() -> None:
    """Explicit temperature, seed, and max_tokens arguments are forwarded
    to the completion request."""
    with patch("qa_agent.llm_client.OpenAI") as MockOpenAI:
        mock_client = MockOpenAI.return_value
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "pong"
        mock_client.chat.completions.create.return_value = mock_response

        chat("reply with pong", "ping", temperature=0.0, seed=42, max_tokens=256)

    request_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert request_kwargs["temperature"] == 0.0
    assert request_kwargs["seed"] == 42
    assert request_kwargs["max_tokens"] == 256


def test_chat_falls_back_to_settings_generation_params(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When no arguments are given, generation params resolve from settings."""
    from qa_agent.config import settings

    monkeypatch.setattr(settings, "llm_temperature", 0.7)
    monkeypatch.setattr(settings, "llm_seed", 7)
    monkeypatch.setattr(settings, "llm_max_tokens", 128)

    with patch("qa_agent.llm_client.OpenAI") as MockOpenAI:
        mock_client = MockOpenAI.return_value
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "pong"
        mock_client.chat.completions.create.return_value = mock_response

        chat("reply with pong", "ping")

    request_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert request_kwargs["temperature"] == 0.7
    assert request_kwargs["seed"] == 7
    assert request_kwargs["max_tokens"] == 128


def test_chat_uses_injected_client_and_model() -> None:
    """An injected client is used as-is (no OpenAI construction) and the
    model override is sent instead of settings.model_name."""
    injected = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "pong"
    injected.chat.completions.create.return_value = mock_response

    with patch("qa_agent.llm_client.OpenAI") as MockOpenAI:
        result = chat("reply with pong", "ping", client=injected, model="other-model")

    assert result == "pong"
    MockOpenAI.assert_not_called()
    request_kwargs = injected.chat.completions.create.call_args.kwargs
    assert request_kwargs["model"] == "other-model"
