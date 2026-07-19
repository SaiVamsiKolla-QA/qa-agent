from unittest.mock import patch

from evaluation.datasets.schema import GoldenCase
from evaluation.runners import agent_runner
from qa_agent.agents.qa_expert import AgentResult

_CASE = GoldenCase.model_validate(
    {
        "id": "q01",
        "question": "What is metamorphic testing?",
        "expected_answer": "A reference answer.",
    }
)

_RESULT = AgentResult(
    answer="test answer",
    retrieved=[
        {
            "text": "First chunk.",
            "score": 0.6,
            "source_doc": "doc.pdf",
            "page": 1,
            "chunk_index": 0,
            "chunk_id": "c1",
        },
        {
            "text": "Second chunk.",
            "score": 0.5,
            "source_doc": "doc.pdf",
            "page": 2,
            "chunk_index": 1,
            "chunk_id": "c2",
        },
    ],
    abstained=False,
    system_prompt="system",
    user_message="user",
    model_name="test-model",
    latency_s=0.01,
)


def test_run_case_wraps_agent_result() -> None:
    """run_case calls the real agent once and pairs case with trace."""
    with patch(
        "evaluation.runners.agent_runner.qa_expert.answer", return_value=_RESULT
    ) as mock_answer:
        run = agent_runner.run_case(_CASE)

    mock_answer.assert_called_once_with(_CASE.question)
    assert run.case_id == "q01"
    assert run.agent is _RESULT


def test_to_llm_test_case_maps_trace_fields() -> None:
    """LLMTestCase gets question, answer, expected answer, and chunk texts."""
    run = agent_runner.CaseRun(
        case_id="q01",
        question=_CASE.question,
        expected_behavior="answer",
        agent=_RESULT,
    )
    test_case = agent_runner.to_llm_test_case(run, _CASE)

    assert test_case.input == _CASE.question
    assert test_case.actual_output == "test answer"
    assert test_case.expected_output == "A reference answer."
    assert test_case.retrieval_context == ["First chunk.", "Second chunk."]


def test_run_record_serializes_full_trace() -> None:
    """run_record output is JSON-safe and carries the whole AgentResult."""
    import json

    run = agent_runner.CaseRun(
        case_id="q01",
        question=_CASE.question,
        expected_behavior="answer",
        agent=_RESULT,
    )
    record = agent_runner.run_record(run)

    json.dumps(record)
    assert record["case_id"] == "q01"
    assert record["agent"]["abstained"] is False
    assert record["agent"]["retrieved"][0]["chunk_id"] == "c1"
