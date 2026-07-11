"""Threshold-gated evals, scaffolded for DeepEval.

Two layers, both under the `eval_gate` marker:

- Schema layer: every case in evals/golden/ must conform to
  golden_set.schema.json. Deterministic, CPU-only, runs anywhere —
  this is the part CI exercises today.
- Live layer: runs the real RAG pipeline per case and fails the gate when
  a DeepEval metric score drops below that case's threshold. Skips when
  mimik is unreachable, same convention as the golden suite.

Unlike tests/golden/ (an evaluation harness whose results are documented,
never gating), these tests are meant to fail builds once thresholds are
calibrated against a stable baseline.
"""

import json
from pathlib import Path

import pytest

EVALS_DIR = Path(__file__).parent
CASE_FILES = sorted((EVALS_DIR / "golden").glob("*.json"))

pytestmark = pytest.mark.eval_gate


def _load(path: Path) -> dict:
    """Read one JSON document from disk."""
    return json.loads(path.read_text())


@pytest.mark.parametrize("case_file", CASE_FILES, ids=lambda p: p.stem)
def test_case_conforms_to_schema(case_file: Path) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = _load(EVALS_DIR / "golden_set.schema.json")

    jsonschema.validate(_load(case_file), schema)


@pytest.mark.parametrize("case_file", CASE_FILES, ids=lambda p: p.stem)
def test_answer_meets_keyword_coverage_threshold(
    case_file: Path, require_mimik: None
) -> None:
    pytest.importorskip("deepeval")
    from deepeval.test_case import LLMTestCase

    from evals.metrics import KeywordCoverageMetric
    from qa_agent.agents.qa_expert import answer

    case = _load(case_file)
    test_case = LLMTestCase(
        input=case["question"],
        actual_output=answer(case["question"]),
    )
    metric = KeywordCoverageMetric(
        expected_keywords=case["expected_keywords"],
        threshold=case["thresholds"]["keyword_coverage"],
    )
    metric.measure(test_case)

    assert metric.is_successful(), (
        f"{case['id']}: keyword coverage {metric.score:.2f} below "
        f"threshold {metric.threshold:.2f}"
    )
