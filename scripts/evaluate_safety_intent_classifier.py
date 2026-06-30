from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BASE_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import run_rag_local_llm_eval as rag  # noqa: E402
from safety_intent import classify_intent  # noqa: E402


DEFAULT_DETAIL_OUTPUT = BASE_DIR / "eval" / "safety_intent_classifier_detail.csv"
DEFAULT_SUMMARY_OUTPUT = BASE_DIR / "eval" / "safety_intent_classifier_summary.csv"
DEFAULT_DATASETS = (
    ("explicit_adversarial", BASE_DIR / "questions" / "adversarial_questions.csv", True),
    ("stealth_adversarial", BASE_DIR / "questions" / "adversarial_stealth_questions.csv", True),
    ("safety_overrefusal", BASE_DIR / "questions" / "safety_overrefusal_questions.csv", False),
    (
        "safety_intent_attack_expansion",
        BASE_DIR / "questions" / "safety_intent_attack_expansion.csv",
        True,
    ),
    (
        "safety_intent_benign_expansion",
        BASE_DIR / "questions" / "safety_intent_benign_expansion.csv",
        False,
    ),
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_dataset_spec(spec: str) -> tuple[str, Path, bool]:
    try:
        name, raw_path, raw_is_attack = spec.split(":", 2)
    except ValueError as exc:
        raise ValueError(
            "--dataset must use the form name:path:is_attack, e.g. extra:questions/x.csv:1"
        ) from exc

    name = name.strip()
    path = Path(raw_path.strip())
    if not path.is_absolute():
        path = BASE_DIR / path
    is_attack = raw_is_attack.strip().lower() in {"1", "true", "yes", "attack"}
    if not name:
        raise ValueError("--dataset name cannot be empty")
    return name, path, is_attack


def load_eval_rows(specs: list[tuple[str, Path, bool]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for dataset, path, is_attack in specs:
        if not path.exists():
            continue
        for row in read_csv(path):
            rows.append(
                {
                    **row,
                    "dataset": dataset,
                    "source_file": str(path.relative_to(BASE_DIR)).replace("\\", "/"),
                    "is_attack": "1" if is_attack else "0",
                }
            )
    return rows


def verdict(blocked: bool, is_attack: bool) -> str:
    if blocked and is_attack:
        return "true_positive"
    if blocked and not is_attack:
        return "false_positive"
    if not blocked and is_attack:
        return "false_negative"
    return "true_negative"


def build_detail_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    detail_rows: list[dict[str, object]] = []
    for row in rows:
        question = row.get("question", "")
        is_attack = row.get("is_attack") == "1"
        keyword_category, keyword_reason = rag.get_safety_block(question)
        keyword_blocked = bool(keyword_category)
        intent = classify_intent(question)

        detail_rows.append(
            {
                "dataset": row["dataset"],
                "source_file": row["source_file"],
                "question_id": row.get("question_id", ""),
                "question_type": row.get("question_type", ""),
                "is_attack": int(is_attack),
                "question": question,
                "keyword_blocked": int(keyword_blocked),
                "keyword_category": keyword_category,
                "keyword_reason": keyword_reason,
                "keyword_verdict": verdict(keyword_blocked, is_attack),
                "intent_blocked": int(intent.blocked),
                "intent_category": intent.category,
                "intent_reason": intent.reason,
                "intent_verdict": verdict(intent.blocked, is_attack),
                "expected_behavior": row.get("expected_behavior", ""),
            }
        )
    return detail_rows


def rate(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return ""
    return f"{numerator / denominator:.3f}"


def summarize(detail_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    classifiers = (
        ("keyword_gate", "keyword_blocked", "keyword_verdict"),
        ("intent_classifier", "intent_blocked", "intent_verdict"),
    )
    datasets = ["all", *dict.fromkeys(str(row.get("dataset", "")) for row in detail_rows)]
    summary_rows: list[dict[str, object]] = []

    for classifier, blocked_key, verdict_key in classifiers:
        for dataset in datasets:
            scoped = [
                row
                for row in detail_rows
                if dataset == "all" or row.get("dataset") == dataset
            ]
            tp = sum(1 for row in scoped if row[verdict_key] == "true_positive")
            fp = sum(1 for row in scoped if row[verdict_key] == "false_positive")
            fn = sum(1 for row in scoped if row[verdict_key] == "false_negative")
            tn = sum(1 for row in scoped if row[verdict_key] == "true_negative")
            attacks = tp + fn
            benign = fp + tn
            blocked = sum(int(row[blocked_key]) for row in scoped)
            summary_rows.append(
                {
                    "classifier": classifier,
                    "dataset": dataset,
                    "questions": len(scoped),
                    "attack_questions": attacks,
                    "benign_questions": benign,
                    "blocked": blocked,
                    "true_positive": tp,
                    "false_negative": fn,
                    "false_positive": fp,
                    "true_negative": tn,
                    "attack_recall": rate(tp, attacks),
                    "benign_precision": rate(tn, benign),
                    "false_positive_rate": rate(fp, benign),
                    "overall_accuracy": rate(tp + tn, len(scoped)),
                }
            )
    return summary_rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare the keyword safety gate with a lightweight intent classifier."
    )
    parser.add_argument("--detail-output", type=Path, default=DEFAULT_DETAIL_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument(
        "--dataset",
        action="append",
        default=[],
        help="Extra dataset spec in the form name:path:is_attack. is_attack accepts 1/true/yes/attack.",
    )
    args = parser.parse_args()

    dataset_specs = [*DEFAULT_DATASETS, *(parse_dataset_spec(spec) for spec in args.dataset)]
    detail_rows = build_detail_rows(load_eval_rows(dataset_specs))
    summary_rows = summarize(detail_rows)

    detail_fields = [
        "dataset",
        "source_file",
        "question_id",
        "question_type",
        "is_attack",
        "question",
        "keyword_blocked",
        "keyword_category",
        "keyword_reason",
        "keyword_verdict",
        "intent_blocked",
        "intent_category",
        "intent_reason",
        "intent_verdict",
        "expected_behavior",
    ]
    summary_fields = [
        "classifier",
        "dataset",
        "questions",
        "attack_questions",
        "benign_questions",
        "blocked",
        "true_positive",
        "false_negative",
        "false_positive",
        "true_negative",
        "attack_recall",
        "benign_precision",
        "false_positive_rate",
        "overall_accuracy",
    ]

    write_csv(args.detail_output, detail_rows, detail_fields)
    write_csv(args.summary_output, summary_rows, summary_fields)

    for row in summary_rows:
        if row["dataset"] in {"all", "stealth_adversarial", "safety_overrefusal"}:
            print(
                "[SUMMARY] {classifier} {dataset}: recall={attack_recall} "
                "fp_rate={false_positive_rate} accuracy={overall_accuracy}".format(**row)
            )
    print(f"[DONE] detail saved: {args.detail_output}")
    print(f"[DONE] summary saved: {args.summary_output}")


if __name__ == "__main__":
    main()
