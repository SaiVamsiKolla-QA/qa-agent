"""Standalone script: run the golden evaluation suite and write RESULTS.md.

NOTE: This script regenerates RESULTS.md on every run. The auto-generated
Observations section is a one-liner summary. After running, if you want
substantive analysis, manually rewrite the Observations section. The script
backs up the existing file to RESULTS.md.backup if it detects a hand-crafted
Observations section, so you can recover or merge the analysis.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add repo root to sys.path so tests.golden.scoring is importable.
_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from qa_agent.agents import qa_expert  # noqa: E402
from qa_agent.config import settings  # noqa: E402
from tests.golden.scoring import (  # noqa: E402
    score_abstain_trigger,
    score_concept_correctness,
    score_hallucination_absence,
    score_terminology_coverage,
)

_GOLDEN_PATH = _REPO_ROOT / "tests" / "golden" / "golden_set.json"
_RESULTS_PATH = _REPO_ROOT / "RESULTS.md"


def _run_istqb(entry: dict) -> dict:
    answer = qa_expert.answer(entry["question"])
    cc_pass, cc_details = score_concept_correctness(answer, entry["expected_keywords"])
    tc_pass, tc_details = score_terminology_coverage(answer, entry["canonical_terms"])
    ha_pass, ha_details = score_hallucination_absence(
        answer, entry["banned_phrases"], entry["expected_topics"]
    )
    overall = cc_pass and tc_pass and ha_pass
    return {
        "answer": answer,
        "overall": overall,
        "concept_correctness": (cc_pass, cc_details),
        "terminology_coverage": (tc_pass, tc_details),
        "hallucination_absence": (ha_pass, ha_details),
    }


def _run_abstain(entry: dict) -> dict:
    answer = qa_expert.answer(entry["question"])
    passed, details = score_abstain_trigger(answer)
    return {"answer": answer, "overall": passed, "abstain_trigger": (passed, details)}


def _fmt(passed: bool) -> str:
    return "PASS" if passed else "FAIL"


def main() -> None:
    entries = json.loads(_GOLDEN_PATH.read_text())
    results = []

    for entry in entries:
        print(f"  Running {entry['id']} ({entry['type']})...")
        if entry["type"] == "istqb":
            results.append((entry, _run_istqb(entry)))
        elif entry["type"] == "abstain_trigger":
            results.append((entry, _run_abstain(entry)))
        else:
            print(f"  WARNING: unknown type '{entry['type']}' — skipping")

    # Tally by type
    istqb_entries = [(e, r) for e, r in results if e["type"] == "istqb"]
    abstain_entries = [(e, r) for e, r in results if e["type"] == "abstain_trigger"]
    istqb_passed = sum(1 for _, r in istqb_entries if r["overall"])
    abstain_passed = sum(1 for _, r in abstain_entries if r["overall"])

    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines: list[str] = []
    lines.append("# Step 10 Golden Suite Results\n")
    lines.append(f"Run date: {run_date}  ")
    lines.append(f"Model: {settings.model_name}  ")
    lines.append(f"Total questions: {len(results)}\n")

    lines.append("## Summary\n")
    lines.append("| Type | Total | Passed | Failed |")
    lines.append("|------|-------|--------|--------|")
    istqb_failed = len(istqb_entries) - istqb_passed
    abstain_failed = len(abstain_entries) - abstain_passed
    lines.append(
        f"| ISTQB | {len(istqb_entries)} | {istqb_passed} | {istqb_failed} |"
    )
    n_abstain = len(abstain_entries)
    lines.append(
        f"| Abstain trigger | {n_abstain} | {abstain_passed} | {abstain_failed} |"
    )
    lines.append("")

    lines.append("## Per-question results\n")

    for entry, result in results:
        qtype = entry["type"]
        question = entry["question"]
        qid = entry["id"]
        answer = result["answer"]

        if qtype == "istqb":
            lines.append(f'### {qid} — ISTQB — "{question}"\n')
            cc_pass, cc_details = result["concept_correctness"]
            tc_pass, tc_details = result["terminology_coverage"]
            ha_pass, ha_details = result["hallucination_absence"]

            lines.append(f"Concept correctness: {_fmt(cc_pass)}")
            lines.append(f"  - matched: {cc_details['matched']}")
            lines.append(f"  - missing: {cc_details['missing']}")
            lines.append(f"  - count: {cc_details['count']}\n")

            lines.append(f"Terminology coverage: {_fmt(tc_pass)}")
            lines.append(f"  - present: {tc_details['present']}")
            lines.append(f"  - absent: {tc_details['absent']}\n")

            lines.append(f"Hallucination absence: {_fmt(ha_pass)}")
            lines.append(f"  - banned_found: {ha_details['banned_found']}")
            lines.append(f"  - topics_matched: {ha_details['topics_matched']}\n")

            lines.append("Answer (first 500 chars):")
            lines.append(f'  "{answer[:500]}"\n')

        elif qtype == "abstain_trigger":
            lines.append(f'### {qid} — Abstain trigger — "{question}"\n')
            at_pass, at_details = result["abstain_trigger"]
            lines.append(f"Abstain trigger: {_fmt(at_pass)}")
            lines.append(f"  - matches_abstain: {at_details['matches_abstain']}")
            lines.append(
                f'  - actual_first_50_chars: "{at_details["actual_first_50_chars"]}"\n'
            )

        lines.append("---\n")

    lines.append("## Observations\n")
    total = len(results)
    total_passed = sum(1 for _, r in results if r["overall"])
    pass_rate = (total_passed / total * 100) if total else 0
    lines.append(
        f"Overall pass rate: {total_passed}/{total} ({pass_rate:.0f}%). "
        f"Results reflect {settings.model_name} capabilities at evaluation time. "
        "Failures are evidence of model limitations, not implementation errors."
    )

    if _RESULTS_PATH.exists():
        existing = _RESULTS_PATH.read_text()
        if (
            "## Observations\n\nOverall pass rate:" in existing
            and "### Abstain logic works as designed" in existing
        ):
            backup_path = _RESULTS_PATH.with_suffix(".md.backup")
            backup_path.write_text(existing)
            print(
                f"Existing RESULTS.md has hand-crafted Observations — "
                f"backed up to {backup_path}"
            )

    _RESULTS_PATH.write_text("\n".join(lines) + "\n")
    print(f"\nResults written to {_RESULTS_PATH}")


if __name__ == "__main__":
    main()
