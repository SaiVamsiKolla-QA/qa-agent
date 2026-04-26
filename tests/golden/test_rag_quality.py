"""Step 10 golden evaluation harness — keyword-matching RAG quality tests."""

import json
from pathlib import Path

import pytest

from qa_agent.agents import qa_expert
from tests.golden.scoring import (
    score_abstain_trigger,
    score_concept_correctness,
    score_hallucination_absence,
    score_terminology_coverage,
)

pytestmark = [pytest.mark.golden]

_GOLDEN_PATH = Path(__file__).parent / "golden_set.json"
_entries = json.loads(_GOLDEN_PATH.read_text())


@pytest.mark.parametrize("entry", _entries, ids=[e["id"] for e in _entries])
def test_istqb_question(entry: dict) -> None:
    """Evaluate ISTQB concept questions on correctness, terminology, and hallucination."""
    if entry["type"] != "istqb":
        pytest.skip("not an istqb entry")

    answer = qa_expert.answer(entry["question"])

    failures = []

    cc_pass, cc_details = score_concept_correctness(answer, entry["expected_keywords"])
    if not cc_pass:
        failures.append(f"Concept correctness FAIL: {cc_details}")

    tc_pass, tc_details = score_terminology_coverage(answer, entry["canonical_terms"])
    if not tc_pass:
        failures.append(f"Terminology coverage FAIL: {tc_details}")

    ha_pass, ha_details = score_hallucination_absence(
        answer, entry["banned_phrases"], entry["expected_topics"]
    )
    if not ha_pass:
        failures.append(f"Hallucination absence FAIL: {ha_details}")

    if failures:
        preview = answer[:300]
        pytest.fail("\n".join(failures) + f"\n\nAnswer (first 300 chars):\n{preview}")


@pytest.mark.parametrize("entry", _entries, ids=[e["id"] for e in _entries])
def test_abstain_trigger(entry: dict) -> None:
    """Verify that out-of-scope questions trigger the abstain response."""
    if entry["type"] != "abstain_trigger":
        pytest.skip("not an abstain_trigger entry")

    answer = qa_expert.answer(entry["question"])
    passed, details = score_abstain_trigger(answer)
    assert passed, f"Expected abstain message, got: {details}"
