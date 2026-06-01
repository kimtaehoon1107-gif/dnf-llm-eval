from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = BASE_DIR / "eval" / "retrieval_compare_summary.csv"
DEFAULT_DETAIL_OUTPUT = BASE_DIR / "eval" / "retrieval_compare_detail.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    text = text.lower()
    words = re.findall(r"[가-힣]+|[a-zA-Z]+|\d+", text)
    tokens: list[str] = []

    for word in words:
        tokens.append(word)
        if re.search(r"[가-힣]", word):
            for n in (2, 3):
                if len(word) >= n:
                    tokens.extend(word[i : i + n] for i in range(len(word) - n + 1))

    return tokens


def split_evidence_parts(evidence: str) -> list[str]:
    parts = [part.strip() for part in evidence.split("/") if part.strip()]
    return parts if parts else [evidence.strip()]


def phrase_hit_ratio(evidence: str, context: str) -> tuple[int, int, float]:
    parts = split_evidence_parts(evidence)
    normalized_context = normalize_text(context)
    hit_count = 0

    for part in parts:
        normalized_part = normalize_text(part)
        if normalized_part and normalized_part in normalized_context:
            hit_count += 1

    total = len(parts)
    ratio = hit_count / total if total else 0.0
    return hit_count, total, ratio


def token_recall(evidence: str, context: str) -> float:
    evidence_tokens = {
        token
        for token in tokenize(evidence)
        if len(token) >= 2 and not token.isdigit()
    }
    if not evidence_tokens:
        return 0.0

    context_tokens = set(tokenize(context))
    matched = sum(1 for token in evidence_tokens if token in context_tokens)
    return matched / len(evidence_tokens)


def first_context_block(context: str) -> str:
    if "\n\n[근거 2]" in context:
        return context.split("\n\n[근거 2]", 1)[0]
    return context


def evidence_hit(phrase_ratio: float, recall: float) -> bool:
    return phrase_ratio >= 0.5 or recall >= 0.65


def parse_run_arg(value: str) -> tuple[str, Path]:
    if "=" not in value:
        path = Path(value)
        return path.stem, path

    label, path_text = value.split("=", 1)
    return label.strip(), Path(path_text)


def make_detail_rows(runs: list[tuple[str, Path]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for label, path in runs:
        for row in read_csv(path):
            evidence = row.get("evidence", "")
            context = row.get("retrieved_context", "")
            top1_context = first_context_block(context)

            phrase_hits, phrase_total, phrase_ratio = phrase_hit_ratio(evidence, context)
            top1_phrase_hits, top1_phrase_total, top1_phrase_ratio = phrase_hit_ratio(
                evidence,
                top1_context,
            )
            recall = token_recall(evidence, context)
            top1_recall = token_recall(evidence, top1_context)

            rows.append(
                {
                    "retriever": label,
                    "question_id": row.get("question_id", ""),
                    "doc_id": row.get("doc_id", ""),
                    "question_type": row.get("question_type", ""),
                    "difficulty": row.get("difficulty", ""),
                    "question": row.get("question", ""),
                    "retrieved_chunk_ids": row.get("retrieved_chunk_ids", ""),
                    "top1_chunk_id": row.get("retrieved_chunk_ids", "").split("|")[0],
                    "phrase_hits": phrase_hits,
                    "phrase_total": phrase_total,
                    "phrase_hit_ratio": f"{phrase_ratio:.3f}",
                    "token_recall": f"{recall:.3f}",
                    "evidence_hit": int(evidence_hit(phrase_ratio, recall)),
                    "top1_phrase_hits": top1_phrase_hits,
                    "top1_phrase_total": top1_phrase_total,
                    "top1_phrase_hit_ratio": f"{top1_phrase_ratio:.3f}",
                    "top1_token_recall": f"{top1_recall:.3f}",
                    "top1_evidence_hit": int(evidence_hit(top1_phrase_ratio, top1_recall)),
                    "status": row.get("status", ""),
                    "error": row.get("error", ""),
                }
            )

    return rows


def summarize(detail_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in detail_rows:
        grouped[str(row["retriever"])].append(row)

    summary_rows: list[dict[str, object]] = []

    for retriever, rows in grouped.items():
        total = len(rows)
        evidence_hits = sum(int(row["evidence_hit"]) for row in rows)
        top1_hits = sum(int(row["top1_evidence_hit"]) for row in rows)
        avg_recall = sum(float(row["token_recall"]) for row in rows) / max(total, 1)
        avg_top1_recall = sum(float(row["top1_token_recall"]) for row in rows) / max(total, 1)
        avg_phrase_ratio = sum(float(row["phrase_hit_ratio"]) for row in rows) / max(total, 1)
        avg_top1_phrase_ratio = sum(float(row["top1_phrase_hit_ratio"]) for row in rows) / max(total, 1)

        summary_rows.append(
            {
                "retriever": retriever,
                "questions": total,
                "evidence_hit_count": evidence_hits,
                "evidence_hit_rate": f"{evidence_hits / max(total, 1):.3f}",
                "top1_evidence_hit_count": top1_hits,
                "top1_evidence_hit_rate": f"{top1_hits / max(total, 1):.3f}",
                "avg_token_recall": f"{avg_recall:.3f}",
                "avg_top1_token_recall": f"{avg_top1_recall:.3f}",
                "avg_phrase_hit_ratio": f"{avg_phrase_ratio:.3f}",
                "avg_top1_phrase_hit_ratio": f"{avg_top1_phrase_ratio:.3f}",
            }
        )

    summary_rows.sort(key=lambda item: str(item["retriever"]))
    return summary_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run",
        action="append",
        required=True,
        help="Retrieval run as label=path. Can be passed multiple times.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--detail-output", type=Path, default=DEFAULT_DETAIL_OUTPUT)
    args = parser.parse_args()

    runs = [parse_run_arg(value) for value in args.run]
    detail_rows = make_detail_rows(runs)
    summary_rows = summarize(detail_rows)

    detail_fields = [
        "retriever",
        "question_id",
        "doc_id",
        "question_type",
        "difficulty",
        "question",
        "retrieved_chunk_ids",
        "top1_chunk_id",
        "phrase_hits",
        "phrase_total",
        "phrase_hit_ratio",
        "token_recall",
        "evidence_hit",
        "top1_phrase_hits",
        "top1_phrase_total",
        "top1_phrase_hit_ratio",
        "top1_token_recall",
        "top1_evidence_hit",
        "status",
        "error",
    ]
    summary_fields = [
        "retriever",
        "questions",
        "evidence_hit_count",
        "evidence_hit_rate",
        "top1_evidence_hit_count",
        "top1_evidence_hit_rate",
        "avg_token_recall",
        "avg_top1_token_recall",
        "avg_phrase_hit_ratio",
        "avg_top1_phrase_hit_ratio",
    ]

    write_csv(args.detail_output, detail_rows, detail_fields)
    write_csv(args.output, summary_rows, summary_fields)

    print(f"[DONE] detail saved: {args.detail_output}")
    print(f"[DONE] summary saved: {args.output}")

    for row in summary_rows:
        print(
            "[SUMMARY] "
            f"{row['retriever']} hit={row['evidence_hit_count']}/{row['questions']} "
            f"top1={row['top1_evidence_hit_count']}/{row['questions']} "
            f"avg_recall={row['avg_token_recall']}"
        )


if __name__ == "__main__":
    main()
