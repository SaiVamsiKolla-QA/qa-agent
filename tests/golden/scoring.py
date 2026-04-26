"""Keyword-matching scoring functions for the Step 10 golden evaluation harness."""

from qa_agent.agents.qa_expert import ABSTAIN_MESSAGE

MIN_KEYWORDS_REQUIRED: int = 3
MIN_TOPICS_REQUIRED: int = 1


def score_concept_correctness(
    answer: str, expected_keywords: list[str]
) -> tuple[bool, dict]:
    """Check that the answer contains enough expected keywords.

    Args:
        answer: The LLM-generated answer text.
        expected_keywords: Substrings that should appear in a correct answer.

    Returns:
        (passed, details) where details has keys 'matched', 'missing', 'count'.
    """
    lower = answer.lower()
    matched = [kw for kw in expected_keywords if kw.lower() in lower]
    missing = [kw for kw in expected_keywords if kw.lower() not in lower]
    passed = len(matched) >= MIN_KEYWORDS_REQUIRED
    return passed, {"matched": matched, "missing": missing, "count": len(matched)}


def score_terminology_coverage(
    answer: str, canonical_terms: list[str]
) -> tuple[bool, dict]:
    """Check that all canonical ISTQB terms appear in the answer.

    Args:
        answer: The LLM-generated answer text.
        canonical_terms: Required ISTQB vocabulary terms.

    Returns:
        (passed, details) where details has keys 'present', 'absent'.
    """
    lower = answer.lower()
    present = [t for t in canonical_terms if t.lower() in lower]
    absent = [t for t in canonical_terms if t.lower() not in lower]
    passed = len(absent) == 0
    return passed, {"present": present, "absent": absent}


def score_hallucination_absence(
    answer: str, banned_phrases: list[str], expected_topics: list[str]
) -> tuple[bool, dict]:
    """Check that no banned phrases appear and enough expected topics are covered.

    Args:
        answer: The LLM-generated answer text.
        banned_phrases: Phrases that must NOT appear (indicate topic confusion).
        expected_topics: Topic labels that should be reflected in the answer.

    Returns:
        (passed, details) where details has keys 'banned_found', 'topics_matched'.
    """
    lower = answer.lower()
    banned_found = [p for p in banned_phrases if p.lower() in lower]
    topics_matched = [t for t in expected_topics if t.lower() in lower]
    passed = len(banned_found) == 0 and len(topics_matched) >= MIN_TOPICS_REQUIRED
    return passed, {"banned_found": banned_found, "topics_matched": topics_matched}


def score_abstain_trigger(answer: str) -> tuple[bool, dict]:
    """Check that the answer is exactly the abstain message.

    Args:
        answer: The LLM-generated (or short-circuit) answer text.

    Returns:
        (passed, details) where details has keys 'matches_abstain',
        'actual_first_50_chars'.
    """
    stripped = answer.strip()
    matches = stripped == ABSTAIN_MESSAGE
    return matches, {
        "matches_abstain": matches,
        "actual_first_50_chars": stripped[:50],
    }
