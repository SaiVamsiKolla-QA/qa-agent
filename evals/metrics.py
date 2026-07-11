"""Deterministic DeepEval metrics that run on CPU with no LLM judge.

This repo is local-only (no cloud LLM calls, ever), which rules out
DeepEval's LLM-as-judge metrics in their default configuration. These
metrics gate on golden-case expectations instead: exact, reproducible,
and runnable on a CI runner with no GPU and no model download.
"""

from __future__ import annotations

import logging

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

logger = logging.getLogger(__name__)


class KeywordCoverageMetric(BaseMetric):
    """Fraction of expected keywords present in the answer, case-insensitive."""

    def __init__(self, expected_keywords: list[str], threshold: float) -> None:
        """Store the golden case's keywords and its gate threshold.

        Args:
            expected_keywords: Keywords the answer is expected to contain.
            threshold: Minimum coverage fraction (0..1) for the gate to pass.
        """
        self.expected_keywords = expected_keywords
        self.threshold = threshold

    def measure(self, test_case: LLMTestCase) -> float:
        """Score coverage of expected keywords in the actual output."""
        answer = (test_case.actual_output or "").lower()
        hits = [kw for kw in self.expected_keywords if kw.lower() in answer]
        self.score = len(hits) / len(self.expected_keywords)
        self.success = self.score >= self.threshold
        logger.info(
            "eval_metric metric=keyword_coverage score=%.2f threshold=%.2f hits=%d",
            self.score,
            self.threshold,
            len(hits),
        )
        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        """Async variant required by the DeepEval metric interface."""
        return self.measure(test_case)

    def is_successful(self) -> bool:
        """Report whether the last measurement met the threshold."""
        return self.success

    @property
    def __name__(self) -> str:
        return "Keyword Coverage"
