"""Bridge between the evaluation framework and the SUT.

This is the ONLY evaluation module allowed to import qa_agent
(ARCHITECTURE.md §2.3). It runs one golden case through the real agent
and maps the AgentResult trace onto a DeepEval LLMTestCase.

Phase 2 supports live retrieval only; frozen-context replay arrives in
Phase 3 (DECISIONS.md ADR-006).
"""

import logging
from dataclasses import asdict, dataclass

from deepeval.test_case import LLMTestCase

from evaluation.datasets.schema import GoldenCase
from qa_agent.agents import qa_expert
from qa_agent.agents.qa_expert import AgentResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CaseRun:
    """One golden case executed against the agent, with its full trace."""

    case_id: str
    question: str
    expected_behavior: str
    agent: AgentResult


def run_case(case: GoldenCase) -> CaseRun:
    """Execute one golden case against the real agent (live retrieval).

    Args:
        case: A validated golden dataset case.

    Returns:
        A CaseRun pairing the case with the agent's AgentResult trace.

    Raises:
        MimikUnavailableError: If the agent's LLM runtime is unreachable.
    """
    logger.info(f"case_started id={case.id}")
    result = qa_expert.answer(case.question)
    logger.info(
        f"case_finished id={case.id} abstained={result.abstained} "
        f"latency_s={result.latency_s}"
    )
    return CaseRun(
        case_id=case.id,
        question=case.question,
        expected_behavior=case.expected_behavior,
        agent=result,
    )


def to_llm_test_case(run: CaseRun, case: GoldenCase) -> LLMTestCase:
    """Map a CaseRun onto DeepEval's LLMTestCase.

    Args:
        run: The executed case with its AgentResult trace.
        case: The originating golden case (source of expected_answer).

    Returns:
        An LLMTestCase with input, actual_output, optional
        expected_output, and the retrieved chunk texts as
        retrieval_context.
    """
    return LLMTestCase(
        input=run.question,
        actual_output=run.agent.answer,
        expected_output=case.expected_answer,
        retrieval_context=[hit["text"] for hit in run.agent.retrieved],
    )


def run_record(run: CaseRun) -> dict:
    """Serialize a CaseRun to a JSON-safe dict for outputs/cases.jsonl.

    Args:
        run: The executed case.

    Returns:
        A dict with the case id, question, expected behavior, and the
        full AgentResult trace.
    """
    return {
        "case_id": run.case_id,
        "question": run.question,
        "expected_behavior": run.expected_behavior,
        "agent": asdict(run.agent),
    }
