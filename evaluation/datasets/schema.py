"""Pydantic schema for golden dataset v2 (JSONL, one case per line).

A malformed case is a load-time error, never a silently skipped or
mis-scored sample. See DECISIONS.md ADR-002 and ADR-010 for the format
rationale and per-field reasoning in ARCHITECTURE.md.
"""

import json
import logging
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class ExpectedRetrieval(BaseModel):
    """Which document pages a correct retrieval should surface."""

    model_config = ConfigDict(extra="forbid")

    source_doc: str
    pages: list[int]


class GoldenCase(BaseModel):
    """One golden dataset case.

    Phase 2 requires only id + question; Phase 3 populates the reference
    fields (expected_answer, ground_truth_facts, expected_retrieval,
    frozen_context). expected_tools / expected_plan are reserved for
    future tool-using agents and must stay None until one exists.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    version: int = 2
    category: str = "concept_explanation"
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    tags: list[str] = Field(default_factory=list)
    question: str
    expected_behavior: Literal["answer", "abstain"] = "answer"
    expected_answer: str | None = None
    ground_truth_facts: list[str] = Field(default_factory=list)
    expected_retrieval: ExpectedRetrieval | None = None
    frozen_context: str | None = None
    legacy: dict | None = None
    metadata: dict = Field(default_factory=dict)
    expected_tools: list[str] | None = None
    expected_plan: str | None = None


class DatasetError(ValueError):
    """Raised when a dataset file is malformed."""


def load_dataset(path: Path) -> list[GoldenCase]:
    """Load and validate a JSONL golden dataset.

    Args:
        path: Path to a .jsonl file, one JSON case per non-empty line.

    Returns:
        List of validated GoldenCase objects, in file order.

    Raises:
        FileNotFoundError: If the file does not exist.
        DatasetError: If any line is invalid JSON, fails schema
            validation, or a case id appears more than once.
    """
    if not path.exists():
        raise FileNotFoundError(f"dataset not found: path={path}")

    cases: list[GoldenCase] = []
    seen_ids: set[str] = set()

    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DatasetError(f"invalid JSON at {path}:{lineno}: {exc}") from exc
        try:
            case = GoldenCase.model_validate(raw)
        except Exception as exc:
            raise DatasetError(f"schema violation at {path}:{lineno}: {exc}") from exc
        if case.id in seen_ids:
            raise DatasetError(f"duplicate case id '{case.id}' at {path}:{lineno}")
        seen_ids.add(case.id)
        cases.append(case)

    logger.info(f"dataset_loaded path={path} cases={len(cases)}")
    return cases
