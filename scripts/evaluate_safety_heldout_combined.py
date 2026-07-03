from __future__ import annotations

import csv
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BASE_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import run_rag_local_llm_eval as rag  # noqa: E402
from safety_intent import INTENT_GATE_VERSION, classify_intent  # noqa: E402

VERSIONS = ["v1", "v2", "v3", "v4", "v5", "v6"]

# heldout_safety_v5 is where regression_v5 (and therefore rules_v5 / the current
# INTENT_GATE_VERSION) was diagnosed from: v5's own failures were read to build
# regression_v5, which directly produced the current rule set. Re-testing the
# current rules against v5 is circular (not a valid measurement at all) and is
# reported separately, excluded from every pooled scope below.
#
# v1-v4 are NOT circular in that same direct sense, but they are not "blind" for
# the current rules either: rules_v5 is a cumulative product of the v2->v3->v4->v5
# tuning chain, each round folding in fixes derived from the round before it. So
# a high score on v1-v4 reflects backward compatibility / retained coverage of
# previously-diagnosed attack styles, not generalization to unseen attacks. Do not
# call this scope "blind" anywhere in reporting.
CIRCULAR_VERSION_FOR_CURRENT_RULES = "v5"

DETAIL_OUTPUT = BASE_DIR / "eval" / "safety_heldout_combined_detail.csv"
SUMMARY_OUTPUT = BASE_DIR / "eval" / "safety_heldout_combined_summary.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def verdict(blocked: bool, is_attack: bool) -> str:
    if blocked and is_attack:
        return "true_positive"
    if blocked and not is_attack:
        return "false_positive"
    if not blocked and is_attack:
        return "false_negative"
    return "true_negative"


def rate(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return ""
    return f"{numerator / denominator:.3f}"


def main() -> None:
    detail_rows: list[dict[str, object]] = []

    for version in VERSIONS:
        path = BASE_DIR / "questions" / f"heldout_safety_{version}.csv"
        if not path.exists():
            continue
        for row in read_csv(path):
            question = row.get("question", "")
            question_type = row.get("question_type", "")
            is_attack = "benign" not in question_type.lower()

            keyword_category, keyword_reason = rag.get_safety_block(question)
            keyword_blocked = bool(keyword_category)

            intent = classify_intent(question)

            detail_rows.append(
                {
                    "heldout_version": version,
                    "question_id": row.get("question_id", ""),
                    "question_type": question_type,
                    "is_attack": int(is_attack),
                    "question": question,
                    "keyword_blocked": int(keyword_blocked),
                    "keyword_category": keyword_category,
                    "keyword_verdict": verdict(keyword_blocked, is_attack),
                    "intent_blocked": int(intent.blocked),
                    "intent_category": intent.category,
                    "intent_verdict": verdict(intent.blocked, is_attack),
                }
            )

    detail_fields = [
        "heldout_version",
        "question_id",
        "question_type",
        "is_attack",
        "question",
        "keyword_blocked",
        "keyword_category",
        "keyword_verdict",
        "intent_blocked",
        "intent_category",
        "intent_verdict",
    ]
    write_csv(DETAIL_OUTPUT, detail_rows, detail_fields)

    classifiers = (
        ("keyword_gate_current", "keyword_blocked", "keyword_verdict"),
        (f"intent_gate_current_{INTENT_GATE_VERSION}", "intent_blocked", "intent_verdict"),
    )

    non_circular_versions = [v for v in VERSIONS if v != CIRCULAR_VERSION_FOR_CURRENT_RULES]

    summary_rows: list[dict[str, object]] = []
    scopes = [
        "backward_compat_excl_circular_v5",  # v1,v2,v3,v4,v6 -- known-attack retention, NOT a blind estimate
        "all_v1_v6_including_circular_v5",  # reference only, includes the circular v5 leak
        *VERSIONS,
    ]

    for classifier, blocked_key, verdict_key in classifiers:
        for scope in scopes:
            if scope == "backward_compat_excl_circular_v5":
                scoped = [r for r in detail_rows if r["heldout_version"] in non_circular_versions]
            elif scope == "all_v1_v6_including_circular_v5":
                scoped = detail_rows
            else:
                scoped = [r for r in detail_rows if r["heldout_version"] == scope]

            tp = sum(1 for r in scoped if r[verdict_key] == "true_positive")
            fp = sum(1 for r in scoped if r[verdict_key] == "false_positive")
            fn = sum(1 for r in scoped if r[verdict_key] == "false_negative")
            tn = sum(1 for r in scoped if r[verdict_key] == "true_negative")
            attacks = tp + fn
            benign = fp + tn

            summary_rows.append(
                {
                    "classifier": classifier,
                    "scope": scope,
                    "questions": len(scoped),
                    "attack_questions": attacks,
                    "benign_questions": benign,
                    "true_positive": tp,
                    "false_negative": fn,
                    "false_positive": fp,
                    "true_negative": tn,
                    "attack_recall": rate(tp, attacks),
                    "benign_fp_rate": rate(fp, benign),
                }
            )

    summary_fields = [
        "classifier",
        "scope",
        "questions",
        "attack_questions",
        "benign_questions",
        "true_positive",
        "false_negative",
        "false_positive",
        "true_negative",
        "attack_recall",
        "benign_fp_rate",
    ]
    write_csv(SUMMARY_OUTPUT, summary_rows, summary_fields)

    for row in summary_rows:
        if row["scope"] in ("backward_compat_excl_circular_v5", "all_v1_v6_including_circular_v5"):
            print(
                "[SUMMARY] {classifier} scope={scope} n={questions} "
                "recall={attack_recall} ({true_positive}/{attack_questions}) "
                "fp_rate={benign_fp_rate} ({false_positive}/{benign_questions})".format(**row)
            )
    print(f"[DONE] detail saved: {DETAIL_OUTPUT}")
    print(f"[DONE] summary saved: {SUMMARY_OUTPUT}")


if __name__ == "__main__":
    main()
