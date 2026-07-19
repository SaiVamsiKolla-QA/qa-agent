import argparse
from unittest.mock import patch

import pytest

from qa_agent.agents.qa_expert import AgentResult
from qa_agent.cli import _cmd_ask, _cmd_ping
from qa_agent.llm_client import MimikUnavailableError


def test_cmd_ping_prints_reply_on_success(capsys: pytest.CaptureFixture) -> None:
    args = argparse.Namespace()
    with patch("qa_agent.cli.chat", return_value="pong"):
        _cmd_ping(args)
    assert "mimik reachable. model reply: pong" in capsys.readouterr().out


def test_cmd_ping_exits_with_error_on_mimik_unavailable(
    capsys: pytest.CaptureFixture,
) -> None:
    args = argparse.Namespace()
    with patch("qa_agent.cli.chat", side_effect=MimikUnavailableError("test failure")):
        with pytest.raises(SystemExit) as exc_info:
            _cmd_ping(args)
    assert exc_info.value.code == 1
    stderr = capsys.readouterr().err
    assert "Error: mimik is not reachable" in stderr
    assert "test failure" in stderr


def test_cmd_ask_calls_qa_expert_and_prints_result(
    capsys: pytest.CaptureFixture,
) -> None:
    """_cmd_ask prints exactly the answer text of the AgentResult —
    stdout behavior is unchanged by the structured return type."""
    args = argparse.Namespace(question="What is metamorphic testing?")
    result = AgentResult(
        answer="test answer",
        retrieved=[],
        abstained=False,
        system_prompt="system",
        user_message="user",
        model_name="test-model",
        latency_s=0.01,
    )
    with patch("qa_agent.cli.qa_expert.answer", return_value=result) as mock_answer:
        _cmd_ask(args)
    assert capsys.readouterr().out == "test answer\n"
    mock_answer.assert_called_once_with(args.question)


def test_cmd_ask_exits_with_error_on_mimik_unavailable(
    capsys: pytest.CaptureFixture,
) -> None:
    """_cmd_ask handles MimikUnavailableError consistently with _cmd_ping."""
    args = argparse.Namespace(question="What is metamorphic testing?")
    with patch(
        "qa_agent.cli.qa_expert.answer",
        side_effect=MimikUnavailableError("test ask failure"),
    ):
        with pytest.raises(SystemExit) as exc_info:
            _cmd_ask(args)
    assert exc_info.value.code == 1
    stderr = capsys.readouterr().err
    assert "Error: mimik is not reachable" in stderr
    assert "test ask failure" in stderr
