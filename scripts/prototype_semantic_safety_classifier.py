from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BASE_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from run_rag_local_llm_eval import encode_bge_dense, load_bge_m3_model  # noqa: E402

EMBEDDING_MODEL = "BAAI/bge-m3"

# Prototype pools are built only from existing DEV adversarial/benign sets, never
# from any heldout_safety_v*.csv, so evaluating on the held-out sets (especially
# v6, the only genuinely blind one) is not circular.
ATTACK_PROTOTYPE_FILES = [
    "adversarial_questions.csv",
    "adversarial_paraphrase_questions.csv",
    "adversarial_stealth_questions.csv",
    "safety_intent_attack_expansion.csv",
]
BENIGN_PROTOTYPE_FILES = [
    "safety_overrefusal_questions.csv",
    "safety_intent_benign_expansion.csv",
    "benchmark_questions.csv",
]

HELDOUT_VERSIONS = ["v1", "v2", "v3", "v4", "v5", "v6"]

DETAIL_OUTPUT = BASE_DIR / "eval" / "semantic_safety_classifier_detail.csv"
SUMMARY_OUTPUT = BASE_DIR / "eval" / "semantic_safety_classifier_summary.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_prototype_texts(filenames: list[str]) -> list[str]:
    texts: list[str] = []
    for name in filenames:
        path = BASE_DIR / "questions" / name
        if not path.exists():
            continue
        for row in read_csv(path):
            question = row.get("question", "").strip()
            if question:
                texts.append(question)
    return texts


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


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
    t0 = time.time()
    print("[LOAD] loading BGE-M3 embedding model...")
    model = load_bge_m3_model(EMBEDDING_MODEL, use_fp16=False)
    print(f"[LOAD] model ready in {time.time() - t0:.1f}s")

    attack_prototypes = load_prototype_texts(ATTACK_PROTOTYPE_FILES)
    benign_prototypes = load_prototype_texts(BENIGN_PROTOTYPE_FILES)
    print(f"[PROTO] attack prototypes: {len(attack_prototypes)}, benign prototypes: {len(benign_prototypes)}")

    t1 = time.time()
    attack_vecs = encode_bge_dense(model, attack_prototypes, batch_size=16, max_length=256)
    benign_vecs = encode_bge_dense(model, benign_prototypes, batch_size=16, max_length=256)
    print(f"[ENCODE] prototypes encoded in {time.time() - t1:.1f}s")

    detail_rows: list[dict[str, object]] = []

    for version in HELDOUT_VERSIONS:
        path = BASE_DIR / "questions" / f"heldout_safety_{version}.csv"
        if not path.exists():
            continue
        rows = read_csv(path)
        questions = [row.get("question", "") for row in rows]

        t2 = time.time()
        q_vecs = encode_bge_dense(model, questions, batch_size=16, max_length=256)
        print(f"[ENCODE] {version}: {len(questions)} questions in {time.time() - t2:.1f}s")

        for row, q_vec in zip(rows, q_vecs):
            question_type = row.get("question_type", "")
            is_attack = "benign" not in question_type.lower()

            max_attack_sim = max((cosine(q_vec, v) for v in attack_vecs), default=-1.0)
            max_benign_sim = max((cosine(q_vec, v) for v in benign_vecs), default=-1.0)
            blocked = max_attack_sim > max_benign_sim

            detail_rows.append(
                {
                    "heldout_version": version,
                    "question_id": row.get("question_id", ""),
                    "question_type": question_type,
                    "is_attack": int(is_attack),
                    "question": row.get("question", ""),
                    "max_attack_sim": f"{max_attack_sim:.4f}",
                    "max_benign_sim": f"{max_benign_sim:.4f}",
                    "semantic_blocked": int(blocked),
                    "semantic_verdict": verdict(blocked, is_attack),
                }
            )

    detail_fields = [
        "heldout_version",
        "question_id",
        "question_type",
        "is_attack",
        "question",
        "max_attack_sim",
        "max_benign_sim",
        "semantic_blocked",
        "semantic_verdict",
    ]
    write_csv(DETAIL_OUTPUT, detail_rows, detail_fields)

    summary_rows: list[dict[str, object]] = []
    scopes = ["all_v1_v6_combined", *HELDOUT_VERSIONS]
    for scope in scopes:
        if scope == "all_v1_v6_combined":
            scoped = detail_rows
        else:
            scoped = [r for r in detail_rows if r["heldout_version"] == scope]

        tp = sum(1 for r in scoped if r["semantic_verdict"] == "true_positive")
        fp = sum(1 for r in scoped if r["semantic_verdict"] == "false_positive")
        fn = sum(1 for r in scoped if r["semantic_verdict"] == "false_negative")
        tn = sum(1 for r in scoped if r["semantic_verdict"] == "true_negative")
        attacks = tp + fn
        benign = fp + tn

        summary_rows.append(
            {
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
        print(
            "[SUMMARY] scope={scope} n={questions} recall={attack_recall} "
            "({true_positive}/{attack_questions}) fp_rate={benign_fp_rate} "
            "({false_positive}/{benign_questions})".format(**row)
        )
    print(f"[DONE] total time {time.time() - t0:.1f}s")
    print(f"[DONE] detail saved: {DETAIL_OUTPUT}")
    print(f"[DONE] summary saved: {SUMMARY_OUTPUT}")


if __name__ == "__main__":
    main()
