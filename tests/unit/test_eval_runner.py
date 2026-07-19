import json
from pathlib import Path
from unittest.mock import patch

import pytest

from evaluation.runners import eval_runner

_REPO_ROOT = Path(__file__).parent.parent.parent


class _StubMetric:
    """Stands in for a DeepEval metric: fixed score, threshold pass/fail."""

    def __init__(self, score: float, threshold: float = 0.8) -> None:
        self._score = score
        self.threshold = threshold
        self.score: float | None = None
        self.success: bool | None = None
        self.reason = "stub reason"

    def measure(self, test_case) -> None:
        self.score = self._score
        self.success = self._score >= self.threshold


def _fake_results(passed: bool) -> list[dict]:
    return [
        {
            "case_id": "q01",
            "question": "q?",
            "expected_behavior": "answer",
            "agent": {"answer": "a", "abstained": False},
            "metrics": {
                "answerrelevancy": {
                    "score": 0.9 if passed else 0.1,
                    "passed": passed,
                    "threshold": 0.8,
                    "reason": "stub",
                }
            },
        }
    ]


def test_load_config_requires_core_keys(tmp_path) -> None:
    path = tmp_path / "eval.yaml"
    path.write_text("dataset: x\n")
    with pytest.raises(ValueError, match="judge"):
        eval_runner.load_config(path)


def test_committed_config_loads() -> None:
    """The checked-in eval.yaml must always satisfy load_config."""
    config = eval_runner.load_config(
        _REPO_ROOT / "evaluation" / "configs" / "eval.yaml"
    )
    assert "answer_relevancy" in config["metrics"]


def test_build_metrics_rejects_unknown_metric() -> None:
    with pytest.raises(ValueError, match="unknown metric"):
        eval_runner.build_metrics({"metrics": {"made_up_metric": {}}}, judge=object())


def test_evaluate_cases_scores_each_case_with_each_metric() -> None:
    """evaluate_cases runs the agent per case and attaches metric verdicts."""
    from evaluation.datasets.schema import GoldenCase
    from evaluation.runners.agent_runner import CaseRun
    from qa_agent.agents.qa_expert import AgentResult

    case = GoldenCase.model_validate({"id": "q01", "question": "q?"})
    run = CaseRun(
        case_id="q01",
        question="q?",
        expected_behavior="answer",
        agent=AgentResult(
            answer="a",
            retrieved=[],
            abstained=False,
            system_prompt="s",
            user_message="u",
            model_name="m",
            latency_s=0.0,
        ),
    )
    metric = _StubMetric(score=0.9)

    with patch(
        "evaluation.runners.eval_runner.agent_runner.run_case", return_value=run
    ):
        results = eval_runner.evaluate_cases([case], [metric])

    assert len(results) == 1
    verdict = results[0]["metrics"]["_stub"]
    assert verdict["score"] == 0.9
    assert verdict["passed"] is True
    assert verdict["threshold"] == 0.8


def test_write_artifacts_emits_three_files_with_mean_scores(tmp_path) -> None:
    run_dir = eval_runner.write_artifacts(
        tmp_path, "run1", {"run_id": "run1"}, _fake_results(passed=True)
    )

    assert (run_dir / "run_meta.json").exists()
    assert (run_dir / "cases.jsonl").exists()
    scores = json.loads((run_dir / "scores.json").read_text())
    assert scores["answerrelevancy"]["mean"] == 0.9
    assert scores["answerrelevancy"]["count"] == 1


@pytest.mark.parametrize("passed,expected_code", [(True, 0), (False, 1)])
def test_main_exit_code_reflects_thresholds(
    tmp_path, passed: bool, expected_code: int
) -> None:
    """Exit code is the quality gate: 0 when all pass, 1 otherwise."""
    with patch(
        "evaluation.runners.eval_runner.evaluate_cases",
        return_value=_fake_results(passed),
    ):
        code = eval_runner.main(["--output-dir", str(tmp_path), "--case", "q01"])

    assert code == expected_code


def test_main_rejects_unknown_case_id(tmp_path) -> None:
    code = eval_runner.main(["--output-dir", str(tmp_path), "--case", "zzz"])
    assert code == 1
