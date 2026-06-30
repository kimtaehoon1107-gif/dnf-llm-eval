from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ANSWERS = BASE_DIR / "eval" / "rag_v2026_06_hybrid_structured_instruct_answers.csv"
DEFAULT_OUTPUT = BASE_DIR / "eval" / "deepeval_rag_v2026_06_hybrid_structured_cases.jsonl"
SCHEMA_VERSION = "deepeval_rag_case_adapter_v1"

METADATA_COLUMNS = (
    "question_id",
    "doc_id",
    "question_type",
    "difficulty",
    "expected_behavior",
    "checked_at",
    "answer_reference_date",
    "source_reference_date",
    "model",
    "retriever",
    "embedding_model",
    "retrieved_chunk_ids",
    "retrieved_doc_ids",
    "retrieval_scores",
    "structured_record_ids",
    "blocked_category",
    "blocked_reason",
    "safety_gate_mode",
    "intent_category",
    "intent_reason",
    "gate_version",
    "latency_sec",
    "status",
    "error",
)

DEEPEVAL_DOCS = (
    "https://deepeval.com/docs/evaluation-test-cases",
    "https://deepeval.com/docs/metrics-answer-relevancy",
    "https://deepeval.com/docs/metrics-faithfulness",
    "https://deepeval.com/docs/metrics-contextual-relevancy",
    "https://deepeval.com/docs/metrics-contextual-precision",
    "https://deepeval.com/docs/metrics-contextual-recall",
)


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(BASE_DIR).as_posix()
    except ValueError:
        return str(path)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def is_success_row(row: dict[str, str]) -> bool:
    status = row.get("status", "").strip().lower()
    if status:
        return status == "success"
    return bool(row.get("model_answer", "").strip())


def starts_context_block(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("[") and ("chunk_id=" in stripped or "record_id=" in stripped)


def split_context_blocks(text: str) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []

    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if current and starts_context_block(line):
            block = "\n".join(current).strip()
            if block:
                blocks.append(block)
            current = [line]
        else:
            current.append(line)

    block = "\n".join(current).strip()
    if block:
        blocks.append(block)
    return blocks or [text]


def full_prompt_context(row: dict[str, str]) -> str:
    context = row.get("retrieved_context", "").strip()
    structured_context = row.get("structured_context", "").strip()
    if structured_context and structured_context not in context:
        if context:
            return f"{structured_context}\n\n{context}"
        return structured_context
    return context


def non_empty_metadata(row: dict[str, str]) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for column in METADATA_COLUMNS:
        value = row.get(column, "").strip()
        if value:
            metadata[column] = value
    evidence = row.get("evidence", "").strip()
    if evidence:
        metadata["gold_evidence"] = evidence
    return metadata


def build_case(row: dict[str, str], row_number: int) -> dict[str, Any]:
    question_id = row.get("question_id", "").strip()
    name = question_id or f"row_{row_number}"
    context_blocks = split_context_blocks(full_prompt_context(row))
    return {
        "schema_version": SCHEMA_VERSION,
        "name": name,
        "input": row.get("question", "").strip(),
        "actual_output": row.get("model_answer", "").strip(),
        "expected_output": row.get("gold_answer", "").strip(),
        "retrieval_context": context_blocks,
        "metadata": non_empty_metadata(row),
    }


def write_jsonl(path: Path, cases: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def write_manifest(
    path: Path,
    *,
    answers_path: Path,
    output_path: Path,
    cases: list[dict[str, Any]],
    rows: list[dict[str, str]],
    skipped_non_success: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    status_counts = Counter(row.get("status", "").strip() or "missing" for row in rows)
    context_sizes = [len(case["retrieval_context"]) for case in cases]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "source_answers": relative(answers_path),
        "output": relative(output_path),
        "case_count": len(cases),
        "source_row_count": len(rows),
        "skipped_non_success": skipped_non_success,
        "status_counts": dict(sorted(status_counts.items())),
        "retrieval_context_blocks": {
            "min": min(context_sizes) if context_sizes else 0,
            "max": max(context_sizes) if context_sizes else 0,
            "avg": round(sum(context_sizes) / len(context_sizes), 3) if context_sizes else 0,
        },
        "deepeval_mapping": {
            "input": "question",
            "actual_output": "model_answer",
            "expected_output": "gold_answer",
            "retrieval_context": "retrieved_context split into ordered evidence blocks",
            "metadata.gold_evidence": "evidence",
        },
        "recommended_metrics": [
            "AnswerRelevancyMetric",
            "FaithfulnessMetric",
            "ContextualRelevancyMetric",
            "ContextualPrecisionMetric",
            "ContextualRecallMetric",
        ],
        "deepeval_docs": list(DEEPEVAL_DOCS),
    }
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def export_cases(
    answers_path: Path,
    output_path: Path,
    manifest_path: Path,
    include_failed: bool,
    limit: int | None,
    fail_on_empty_context: bool,
) -> tuple[int, int]:
    rows = read_csv_rows(answers_path)
    cases: list[dict[str, Any]] = []
    skipped_non_success = 0

    for row_number, row in enumerate(rows, start=2):
        if not include_failed and not is_success_row(row):
            skipped_non_success += 1
            continue
        case = build_case(row, row_number)
        if fail_on_empty_context and not case["retrieval_context"]:
            raise SystemExit(f"{relative(answers_path)} row {row_number} has empty retrieval_context")
        cases.append(case)
        if limit is not None and len(cases) >= limit:
            break

    write_jsonl(output_path, cases)
    write_manifest(
        manifest_path,
        answers_path=answers_path,
        output_path=output_path,
        cases=cases,
        rows=rows,
        skipped_non_success=skipped_non_success,
    )
    return len(cases), skipped_non_success


def default_manifest_path(output_path: Path) -> Path:
    if output_path.suffix:
        return output_path.with_suffix(".manifest.json")
    return output_path.with_name(f"{output_path.name}.manifest.json")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export RAG answer CSV rows as DeepEval-ready LLMTestCase JSONL records."
    )
    parser.add_argument(
        "--answers",
        type=Path,
        default=DEFAULT_ANSWERS,
        help=f"RAG answer CSV to export. Defaults to {relative(DEFAULT_ANSWERS)}.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"JSONL output path. Defaults to {relative(DEFAULT_OUTPUT)}.",
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=None,
        help="Manifest output path. Defaults to the JSONL path with .manifest.json suffix.",
    )
    parser.add_argument(
        "--include-failed",
        action="store_true",
        help="Include non-success rows such as safety-blocked or failed generations.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Export at most this many cases.")
    parser.add_argument(
        "--fail-on-empty-context",
        action="store_true",
        help="Fail if an exported row has no retrieval_context.",
    )
    args = parser.parse_args()

    answers_path = args.answers if args.answers.is_absolute() else BASE_DIR / args.answers
    output_path = args.output if args.output.is_absolute() else BASE_DIR / args.output
    manifest_path = args.manifest_output
    if manifest_path is None:
        manifest_path = default_manifest_path(output_path)
    elif not manifest_path.is_absolute():
        manifest_path = BASE_DIR / manifest_path

    case_count, skipped_non_success = export_cases(
        answers_path=answers_path,
        output_path=output_path,
        manifest_path=manifest_path,
        include_failed=args.include_failed,
        limit=args.limit,
        fail_on_empty_context=args.fail_on_empty_context,
    )
    print(
        "[OK] exported "
        f"{case_count} DeepEval RAG cases to {relative(output_path)} "
        f"(skipped_non_success={skipped_non_success})"
    )
    print(f"[OK] wrote manifest to {relative(manifest_path)}")


if __name__ == "__main__":
    main()
