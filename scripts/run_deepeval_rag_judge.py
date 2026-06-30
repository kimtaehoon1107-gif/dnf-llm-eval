from __future__ import annotations

import argparse
import csv
import importlib.metadata
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CASES = BASE_DIR / "eval" / "deepeval_rag_v2026_06_hybrid_structured_cases.jsonl"
DEFAULT_OUTPUT = BASE_DIR / "eval" / "deepeval_rag_v2026_06_hybrid_structured_judge.csv"
DEFAULT_SUMMARY_OUTPUT = BASE_DIR / "eval" / "deepeval_rag_v2026_06_hybrid_structured_judge_summary.csv"
DEFAULT_JUDGE_MODEL = "qwen3:4b-instruct-2507-q4_K_M"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_JUDGE_NUM_CTX = 8192
SCHEMA_VERSION = "deepeval_rag_judge_runner_v1"

METRIC_CHOICES = (
    "faithfulness",
    "contextual_relevancy",
    "answer_relevancy",
    "contextual_precision",
    "contextual_recall",
)

DEFAULT_METRICS = (
    "faithfulness",
    "contextual_relevancy",
    "answer_relevancy",
)


@dataclass
class JudgeCase:
    name: str
    input: str
    actual_output: str
    expected_output: str
    retrieval_context: list[str]
    metadata: dict[str, Any]


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(BASE_DIR).as_posix()
    except ValueError:
        return str(path)


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else BASE_DIR / path


def read_jsonl_cases(path: Path) -> list[JudgeCase]:
    cases: list[JudgeCase] = []
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            retrieval_context = record.get("retrieval_context", [])
            if not isinstance(retrieval_context, list):
                raise ValueError(f"{relative(path)} line {line_number} retrieval_context must be a list")
            cases.append(
                JudgeCase(
                    name=str(record.get("name", f"line_{line_number}")),
                    input=str(record.get("input", "")),
                    actual_output=str(record.get("actual_output", "")),
                    expected_output=str(record.get("expected_output", "")),
                    retrieval_context=[str(item) for item in retrieval_context],
                    metadata=record.get("metadata", {}) if isinstance(record.get("metadata", {}), dict) else {},
                )
            )
    return cases


def deepeval_version() -> str:
    try:
        return importlib.metadata.version("deepeval")
    except importlib.metadata.PackageNotFoundError:
        return ""


def require_deepeval() -> dict[str, Any]:
    try:
        from deepeval.metrics import (  # type: ignore
            AnswerRelevancyMetric,
            ContextualPrecisionMetric,
            ContextualRecallMetric,
            ContextualRelevancyMetric,
            FaithfulnessMetric,
        )
        from deepeval.models import OllamaModel  # type: ignore
        from deepeval.test_case import LLMTestCase  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "DeepEval is not installed. Install the optional dependency first:\n"
            "  python -m pip install -r requirements-deepeval.txt\n"
            f"Original error: {exc}"
        ) from exc

    return {
        "AnswerRelevancyMetric": AnswerRelevancyMetric,
        "ContextualPrecisionMetric": ContextualPrecisionMetric,
        "ContextualRecallMetric": ContextualRecallMetric,
        "ContextualRelevancyMetric": ContextualRelevancyMetric,
        "FaithfulnessMetric": FaithfulnessMetric,
        "LLMTestCase": LLMTestCase,
        "OllamaModel": OllamaModel,
    }


def build_ollama_model(
    ollama_model_class: Any,
    model_name: str,
    base_url: str,
    num_ctx: int,
) -> Any:
    generation_kwargs = {"num_ctx": num_ctx} if num_ctx > 0 else {}
    init_attempts = (
        {
            "model": model_name,
            "base_url": base_url,
            "temperature": 0,
            "generation_kwargs": generation_kwargs,
        },
        {"model": model_name, "base_url": base_url, "generation_kwargs": generation_kwargs},
        {"model": model_name, "generation_kwargs": generation_kwargs},
        {"model": model_name, "base_url": base_url},
        {"model": model_name},
    )
    last_error: Exception | None = None
    for kwargs in init_attempts:
        try:
            return ollama_model_class(**kwargs)
        except TypeError as exc:
            last_error = exc
    raise TypeError(f"Could not initialize DeepEval OllamaModel: {last_error}")


def build_metric(metric_name: str, classes: dict[str, Any], model: Any, threshold: float) -> Any:
    metric_classes = {
        "faithfulness": classes["FaithfulnessMetric"],
        "contextual_relevancy": classes["ContextualRelevancyMetric"],
        "answer_relevancy": classes["AnswerRelevancyMetric"],
        "contextual_precision": classes["ContextualPrecisionMetric"],
        "contextual_recall": classes["ContextualRecallMetric"],
    }
    metric_class = metric_classes[metric_name]
    init_attempts = (
        {"threshold": threshold, "model": model, "include_reason": True},
        {"threshold": threshold, "model": model},
        {"model": model},
        {},
    )
    last_error: Exception | None = None
    for kwargs in init_attempts:
        try:
            return metric_class(**kwargs)
        except TypeError as exc:
            last_error = exc
    raise TypeError(f"Could not initialize {metric_class.__name__}: {last_error}")


def build_test_case(case: JudgeCase, llm_test_case_class: Any) -> Any:
    return llm_test_case_class(
        input=case.input,
        actual_output=case.actual_output,
        expected_output=case.expected_output,
        retrieval_context=case.retrieval_context,
    )


def metric_passed(metric: Any, threshold: float) -> str:
    success = getattr(metric, "success", None)
    if success is not None:
        return str(bool(success)).lower()
    score = getattr(metric, "score", None)
    if isinstance(score, (int, float)):
        return str(score >= threshold).lower()
    return ""


def output_fieldnames() -> list[str]:
    return [
        "case_name",
        "question_id",
        "doc_id",
        "question_type",
        "difficulty",
        "metric",
        "score",
        "threshold",
        "passed",
        "reason",
        "error",
        "latency_sec",
        "judge_provider",
        "judge_model",
        "judge_num_ctx",
        "deepeval_version",
        "input",
        "actual_output",
        "expected_output",
        "retrieval_context_blocks",
    ]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames())
        writer.writeheader()
        writer.writerows(rows)


def write_summary_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    by_metric: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_metric.setdefault(row["metric"], []).append(row)

    summary_rows: list[dict[str, str]] = []
    for metric_name, metric_rows in sorted(by_metric.items()):
        scores = [
            float(row["score"])
            for row in metric_rows
            if row.get("score") not in ("", None) and not row.get("error")
        ]
        passed_count = sum(1 for row in metric_rows if row.get("passed") == "true")
        error_count = sum(1 for row in metric_rows if row.get("error"))
        summary_rows.append(
            {
                "metric": metric_name,
                "cases": str(len(metric_rows)),
                "scored": str(len(scores)),
                "passed": str(passed_count),
                "errors": str(error_count),
                "avg_score": f"{sum(scores) / len(scores):.3f}" if scores else "",
                "min_score": f"{min(scores):.3f}" if scores else "",
                "max_score": f"{max(scores):.3f}" if scores else "",
            }
        )

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "metric",
                "cases",
                "scored",
                "passed",
                "errors",
                "avg_score",
                "min_score",
                "max_score",
            ],
        )
        writer.writeheader()
        writer.writerows(summary_rows)


def base_row(
    case: JudgeCase,
    metric_name: str,
    threshold: float,
    judge_provider: str,
    judge_model: str,
    judge_num_ctx: int,
) -> dict[str, str]:
    metadata = case.metadata
    return {
        "case_name": case.name,
        "question_id": str(metadata.get("question_id", "")),
        "doc_id": str(metadata.get("doc_id", "")),
        "question_type": str(metadata.get("question_type", "")),
        "difficulty": str(metadata.get("difficulty", "")),
        "metric": metric_name,
        "score": "",
        "threshold": f"{threshold:.3f}",
        "passed": "",
        "reason": "",
        "error": "",
        "latency_sec": "",
        "judge_provider": judge_provider,
        "judge_model": judge_model,
        "judge_num_ctx": str(judge_num_ctx),
        "deepeval_version": deepeval_version(),
        "input": case.input,
        "actual_output": case.actual_output,
        "expected_output": case.expected_output,
        "retrieval_context_blocks": str(len(case.retrieval_context)),
    }


def run_judge(
    cases: list[JudgeCase],
    metric_names: list[str],
    output_path: Path,
    summary_output_path: Path,
    judge_model_name: str,
    ollama_base_url: str,
    judge_num_ctx: int,
    threshold: float,
    keep_going: bool,
) -> None:
    classes = require_deepeval()
    judge_model = build_ollama_model(
        classes["OllamaModel"],
        judge_model_name,
        ollama_base_url,
        judge_num_ctx,
    )
    metrics = [
        (metric_name, build_metric(metric_name, classes, judge_model, threshold))
        for metric_name in metric_names
    ]

    rows: list[dict[str, str]] = []
    for case in cases:
        test_case = build_test_case(case, classes["LLMTestCase"])
        for metric_name, metric in metrics:
            row = base_row(
                case,
                metric_name,
                threshold,
                "ollama",
                judge_model_name,
                judge_num_ctx,
            )
            start = time.perf_counter()
            try:
                metric.measure(test_case)
                score = getattr(metric, "score", "")
                row["score"] = f"{score:.3f}" if isinstance(score, (int, float)) else str(score)
                row["passed"] = metric_passed(metric, threshold)
                row["reason"] = str(getattr(metric, "reason", "") or "")
            except Exception as exc:  # DeepEval/model exceptions are surfaced in the CSV.
                row["error"] = f"{type(exc).__name__}: {exc}"
                if not keep_going:
                    rows.append(row)
                    write_csv(output_path, rows)
                    write_summary_csv(summary_output_path, rows)
                    raise
            finally:
                row["latency_sec"] = f"{time.perf_counter() - start:.3f}"
            rows.append(row)
            print(
                f"[{case.name}] {metric_name} "
                f"score={row['score'] or 'NA'} passed={row['passed'] or 'NA'} "
                f"error={'yes' if row['error'] else 'no'}"
            )

    write_csv(output_path, rows)
    write_summary_csv(summary_output_path, rows)
    print(f"[OK] wrote {len(rows)} judge rows to {relative(output_path)}")
    print(f"[OK] wrote summary to {relative(summary_output_path)}")


def dry_run(
    cases: list[JudgeCase],
    metric_names: list[str],
    output_path: Path,
    summary_output_path: Path,
    judge_model_name: str,
    judge_num_ctx: int,
    threshold: float,
) -> None:
    rows: list[dict[str, str]] = []
    for case in cases:
        for metric_name in metric_names:
            row = base_row(case, metric_name, threshold, "ollama", judge_model_name, judge_num_ctx)
            row["passed"] = "dry_run"
            rows.append(row)
    write_csv(output_path, rows)
    write_summary_csv(summary_output_path, rows)
    print(f"[DRY-RUN] planned {len(rows)} judge rows from {len(cases)} cases")
    print(f"[DRY-RUN] wrote {relative(output_path)} and {relative(summary_output_path)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run DeepEval RAG metrics over exported JSONL LLMTestCase records."
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_CASES,
        help=f"DeepEval-ready JSONL cases. Defaults to {relative(DEFAULT_CASES)}.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Metric detail CSV output. Defaults to {relative(DEFAULT_OUTPUT)}.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=DEFAULT_SUMMARY_OUTPUT,
        help=f"Metric summary CSV output. Defaults to {relative(DEFAULT_SUMMARY_OUTPUT)}.",
    )
    parser.add_argument(
        "--metrics",
        nargs="+",
        choices=METRIC_CHOICES,
        default=list(DEFAULT_METRICS),
        help="Metrics to run. Defaults to faithfulness/contextual_relevancy/answer_relevancy.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Evaluate at most this many cases.")
    parser.add_argument("--threshold", type=float, default=0.7, help="Metric pass threshold.")
    parser.add_argument(
        "--judge-model",
        default=DEFAULT_JUDGE_MODEL,
        help=f"Ollama judge model name. Defaults to {DEFAULT_JUDGE_MODEL}.",
    )
    parser.add_argument(
        "--ollama-base-url",
        default=DEFAULT_OLLAMA_BASE_URL,
        help=f"Ollama base URL. Defaults to {DEFAULT_OLLAMA_BASE_URL}.",
    )
    parser.add_argument(
        "--judge-num-ctx",
        type=int,
        default=DEFAULT_JUDGE_NUM_CTX,
        help=f"Ollama judge context window. Defaults to {DEFAULT_JUDGE_NUM_CTX}.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate cases and write planned rows without importing or calling DeepEval.",
    )
    parser.add_argument(
        "--keep-going",
        action="store_true",
        help="Continue after a metric/model error and record it in the CSV.",
    )
    args = parser.parse_args()

    cases_path = resolve_path(args.cases)
    output_path = resolve_path(args.output)
    summary_output_path = resolve_path(args.summary_output)
    cases = read_jsonl_cases(cases_path)
    if args.limit is not None:
        cases = cases[: args.limit]

    if not cases:
        raise SystemExit(f"No cases loaded from {relative(cases_path)}")

    metric_names = list(dict.fromkeys(args.metrics))
    if args.dry_run:
        dry_run(
            cases,
            metric_names,
            output_path,
            summary_output_path,
            args.judge_model,
            args.judge_num_ctx,
            args.threshold,
        )
        return

    run_judge(
        cases=cases,
        metric_names=metric_names,
        output_path=output_path,
        summary_output_path=summary_output_path,
        judge_model_name=args.judge_model,
        ollama_base_url=args.ollama_base_url,
        judge_num_ctx=args.judge_num_ctx,
        threshold=args.threshold,
        keep_going=args.keep_going,
    )


if __name__ == "__main__":
    main()
