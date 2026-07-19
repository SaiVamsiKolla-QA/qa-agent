"""Single-model evaluation run: dataset -> agent -> metrics -> artifacts.

Usage:
    poetry run python -m evaluation.runners.eval_runner --case q01
    poetry run python -m evaluation.runners.eval_runner            # all cases

Exit code 0 when every measured metric meets its threshold, 1 otherwise —
the exit code IS the future CI quality gate (ARCHITECTURE.md §2.3).

This module is a CLI entry point, so user-facing print() is allowed here,
mirroring scripts/run_golden.py.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Opt out of DeepEval telemetry before deepeval imports anywhere below.
os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")

import yaml  # noqa: E402
from deepeval.metrics import AnswerRelevancyMetric  # noqa: E402

from evaluation.datasets.schema import GoldenCase, load_dataset  # noqa: E402
from evaluation.models.judge import build_judge  # noqa: E402
from evaluation.runners import agent_runner  # noqa: E402

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).parent.parent.parent
_DEFAULT_CONFIG = _REPO_ROOT / "evaluation" / "configs" / "eval.yaml"
_DEFAULT_OUTPUT_DIR = _REPO_ROOT / "evaluation" / "outputs"


def load_config(path: Path) -> dict:
    """Load and minimally validate eval.yaml.

    Args:
        path: Path to the YAML config.

    Returns:
        The parsed config dict.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If required keys (dataset, judge, metrics) are missing.
    """
    if not path.exists():
        raise FileNotFoundError(f"config not found: path={path}")
    config = yaml.safe_load(path.read_text())
    for key in ("dataset", "judge", "metrics"):
        if key not in config:
            raise ValueError(f"eval config missing required key '{key}': {path}")
    return config


def build_metrics(config: dict, judge) -> list:
    """Build the DeepEval metric list from the config's metrics mapping.

    Phase 2 wires answer_relevancy only; Phase 4 extends this registry.

    Args:
        config: The full eval config dict.
        judge: The judge model passed to every judge-based metric.

    Returns:
        List of configured DeepEval metric instances.

    Raises:
        ValueError: If an unknown metric name appears in the config.
    """
    metrics = []
    for name, metric_cfg in config["metrics"].items():
        if name == "answer_relevancy":
            metrics.append(
                AnswerRelevancyMetric(
                    threshold=metric_cfg.get("threshold", 0.8),
                    model=judge,
                    include_reason=True,
                    async_mode=False,
                )
            )
        else:
            raise ValueError(f"unknown metric in config: {name}")
    return metrics


def _metric_name(metric) -> str:
    """Return a stable snake_case name for a metric instance."""
    return type(metric).__name__.removesuffix("Metric").lower()


def _git_sha() -> str:
    """Return the short git SHA of HEAD, or 'nogit' outside a repo."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "nogit"


def evaluate_cases(cases: list[GoldenCase], metrics: list) -> list[dict]:
    """Run each case through the agent and score it with every metric.

    Args:
        cases: Validated golden cases to run.
        metrics: Configured DeepEval metric instances.

    Returns:
        One result dict per case: the serialized CaseRun plus a
        'metrics' mapping of name -> {score, passed, threshold, reason}.
    """
    results = []
    for case in cases:
        run = agent_runner.run_case(case)
        test_case = agent_runner.to_llm_test_case(run, case)
        record = agent_runner.run_record(run)
        record["metrics"] = {}
        for metric in metrics:
            metric.measure(test_case)
            record["metrics"][_metric_name(metric)] = {
                "score": metric.score,
                "passed": bool(metric.success),
                "threshold": metric.threshold,
                "reason": metric.reason,
            }
        results.append(record)
    return results


def write_artifacts(
    output_dir: Path, run_id: str, run_meta: dict, results: list[dict]
) -> Path:
    """Write run_meta.json, cases.jsonl, and scores.json for one run.

    Args:
        output_dir: Root outputs directory.
        run_id: Unique id for this run (subdirectory name).
        run_meta: Run metadata (config, git sha, timestamps, verdict).
        results: Per-case result dicts from evaluate_cases.

    Returns:
        The run directory that was written.
    """
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "run_meta.json").write_text(json.dumps(run_meta, indent=2))
    (run_dir / "cases.jsonl").write_text(
        "\n".join(json.dumps(r) for r in results) + "\n"
    )

    scores: dict = {}
    for record in results:
        for name, verdict in record["metrics"].items():
            scores.setdefault(name, []).append(verdict["score"])
    summary = {
        name: {
            "mean": round(sum(values) / len(values), 4),
            "count": len(values),
        }
        for name, values in scores.items()
        if values
    }
    (run_dir / "scores.json").write_text(json.dumps(summary, indent=2))
    return run_dir


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns the process exit code (0 pass / 1 fail)."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    parser = argparse.ArgumentParser(
        prog="eval_runner",
        description="Run the golden dataset through the agent and DeepEval.",
    )
    parser.add_argument(
        "--config", type=Path, default=_DEFAULT_CONFIG, help="Path to eval.yaml."
    )
    parser.add_argument(
        "--case",
        action="append",
        default=None,
        help="Case id to run (repeatable). Default: all cases.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_DEFAULT_OUTPUT_DIR,
        help="Directory for run artifacts.",
    )
    args = parser.parse_args(argv)

    config = load_config(args.config)
    cases = load_dataset(_REPO_ROOT / config["dataset"])
    if args.case:
        wanted = set(args.case)
        cases = [c for c in cases if c.id in wanted]
        missing = wanted - {c.id for c in cases}
        if missing:
            print(f"Error: unknown case id(s): {sorted(missing)}", file=sys.stderr)
            return 1
    if not cases:
        print("Error: no cases selected.", file=sys.stderr)
        return 1

    judge = build_judge(config["judge"])
    metrics = build_metrics(config, judge)

    from qa_agent.config import settings
    from qa_agent.llm_client import MimikUnavailableError

    started = datetime.now(timezone.utc)
    run_id = f"{started.strftime('%Y%m%dT%H%M%SZ')}_{_git_sha()}_{settings.model_name}"
    print(f"Run {run_id}: {len(cases)} case(s), judge={judge.get_model_name()}")

    t0 = time.monotonic()
    try:
        results = evaluate_cases(cases, metrics)
    except MimikUnavailableError as exc:
        print(f"Error: agent runtime unreachable — {exc}", file=sys.stderr)
        print("Start it with: mimoe start", file=sys.stderr)
        return 1

    all_passed = all(
        verdict["passed"]
        for record in results
        for verdict in record["metrics"].values()
    )
    run_meta = {
        "run_id": run_id,
        "started": started.isoformat(),
        "duration_s": round(time.monotonic() - t0, 2),
        "git_sha": _git_sha(),
        "agent_model": settings.model_name,
        "judge_model": judge.get_model_name(),
        "config": config,
        "cases": len(results),
        "all_passed": all_passed,
    }
    run_dir = write_artifacts(args.output_dir, run_id, run_meta, results)

    for record in results:
        for name, verdict in record["metrics"].items():
            status = "PASS" if verdict["passed"] else "FAIL"
            print(
                f"  {record['case_id']}  {name}  score={verdict['score']:.2f}  "
                f"threshold={verdict['threshold']}  {status}"
            )
    print(f"Artifacts: {run_dir}")
    print(f"Overall: {'PASS' if all_passed else 'FAIL'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
