from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from evaluation.models.judge import OpenAICompatibleJudge, _extract_json, build_judge


def _mock_completion(text: str) -> MagicMock:
    response = MagicMock()
    response.choices[0].message.content = text
    return response


def test_generate_returns_plain_text() -> None:
    judge = OpenAICompatibleJudge(model="test-judge", base_url="http://local/v1")
    with patch("evaluation.models.judge.OpenAI") as MockOpenAI:
        client = MockOpenAI.return_value
        client.chat.completions.create.return_value = _mock_completion("verdict")

        assert judge.generate("prompt") == "verdict"

    request_kwargs = client.chat.completions.create.call_args.kwargs
    assert request_kwargs["model"] == "test-judge"
    assert request_kwargs["temperature"] == 0.0


def test_generate_parses_schema_from_fenced_reply() -> None:
    """A markdown-fenced JSON reply validates into the given schema."""

    class Verdict(BaseModel):
        score: float

    judge = OpenAICompatibleJudge(model="test-judge", base_url="http://local/v1")
    with patch("evaluation.models.judge.OpenAI") as MockOpenAI:
        client = MockOpenAI.return_value
        client.chat.completions.create.return_value = _mock_completion(
            'Here you go:\n```json\n{"score": 0.9}\n```'
        )

        result = judge.generate("prompt", schema=Verdict)

    assert isinstance(result, Verdict)
    assert result.score == 0.9


def test_load_model_requires_key_for_cloud_openai(monkeypatch) -> None:
    """Cloud OpenAI (base_url=None) without the key env var fails loudly."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    judge = OpenAICompatibleJudge(model="gpt-4.1-mini", base_url=None)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        judge.load_model()


def test_load_model_allows_local_endpoint_without_key(monkeypatch) -> None:
    """Local endpoints work with a placeholder key when the env var is unset."""
    monkeypatch.delenv("LOCAL_JUDGE_KEY", raising=False)
    judge = OpenAICompatibleJudge(
        model="local-judge",
        base_url="http://localhost:11434/v1",
        api_key_env="LOCAL_JUDGE_KEY",
    )
    with patch("evaluation.models.judge.OpenAI") as MockOpenAI:
        judge.load_model()

    assert MockOpenAI.call_args.kwargs["api_key"] == "unused"


def test_extract_json_raises_when_no_object_present() -> None:
    with pytest.raises(ValueError, match="no JSON object"):
        _extract_json("no braces here")


def test_build_judge_reads_config_mapping() -> None:
    judge = build_judge(
        {
            "model": "qwen2.5:14b",
            "base_url": "http://localhost:11434/v1",
            "api_key_env": "OLLAMA_KEY",
            "temperature": 0.0,
        }
    )
    assert judge.get_model_name() == "qwen2.5:14b"
    assert judge.base_url == "http://localhost:11434/v1"
    assert judge.api_key_env == "OLLAMA_KEY"
