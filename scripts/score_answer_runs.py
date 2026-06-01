from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = BASE_DIR / "eval" / "answer_compare_summary.csv"
DEFAULT_DETAIL_OUTPUT = BASE_DIR / "eval" / "answer_compare_detail.csv"

META_PATTERNS = (
    r"\bokay\b",
    r"let'?s tackle",
    r"\bfirst,\b",
    r"i need to",
    r"looking at",
    r"let me",
    r"wait,",
    r"translates to",
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


def content_tokens(text: str) -> set[str]:
    stopwords = {
        "그리고",
        "또는",
        "각각",
        "무엇인가",
        "어떻게",
        "되는가",
        "있는가",
        "설명",
        "알려줘",
        "입니다",
        "합니다",
    }
    return {
        token
        for token in tokenize(text)
        if len(token) >= 2 and token not in stopwords
    }


def token_recall(reference: str, answer: str) -> float:
    reference_tokens = content_tokens(reference)
    if not reference_tokens:
        return 0.0

    answer_tokens = set(tokenize(answer))
    matched = sum(1 for token in reference_tokens if token in answer_tokens)
    return matched / len(reference_tokens)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def phrase_hit_ratio(reference: str, answer: str) -> float:
    parts = [part.strip() for part in reference.split("/") if part.strip()]
    if not parts:
        parts = [reference.strip()]

    normalized_answer = normalize_text(answer)
    hits = 0
    for part in parts:
        if normalize_text(part) in normalized_answer:
            hits += 1

    return hits / len(parts) if parts else 0.0


def has_refusal(answer: str) -> bool:
    return "제공된 문서에서 확인할 수 없습니다" in answer


def has_meta_reasoning(answer: str) -> bool:
    lowered = answer.lower()
    return any(re.search(pattern, lowered) for pattern in META_PATTERNS)


def korean_char_ratio(answer: str) -> float:
    letters = re.findall(r"[가-힣A-Za-z]", answer)
    if not letters:
        return 0.0

    korean = [char for char in letters if re.match(r"[가-힣]", char)]
    return len(korean) / len(letters)


def has_non_korean_cjk(answer: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", answer))


def proxy_pass(
    gold_recall: float,
    evidence_recall: float,
    gold_phrase_ratio: float,
    evidence_phrase_ratio: float,
    refusal: bool,
) -> bool:
    if refusal:
        return False

    return (
        gold_recall >= 0.60
        or evidence_recall >= 0.70
        or gold_phrase_ratio >= 0.50
        or evidence_phrase_ratio >= 0.50
    )


def parse_run_arg(value: str) -> tuple[str, Path]:
    if "=" not in value:
        path = Path(value)
        return path.stem, path

    label, path_text = value.split("=", 1)
    return label.strip(), Path(path_text)


def make_detail_rows(runs: list[tuple[str, Path]]) -> list[dict[str, object]]:
    detail_rows: list[dict[str, object]] = []

    for label, path in runs:
        for row in read_csv(path):
            answer = row.get("model_answer", "")
            gold_answer = row.get("gold_answer", "")
            evidence = row.get("evidence", "")

            gold_recall = token_recall(gold_answer, answer)
            evidence_recall = token_recall(evidence, answer)
            gold_phrase_ratio = phrase_hit_ratio(gold_answer, answer)
            evidence_phrase_ratio = phrase_hit_ratio(evidence, answer)
            refusal = has_refusal(answer)
            meta_reasoning = has_meta_reasoning(answer)
            korean_ratio = korean_char_ratio(answer)
            non_korean_cjk = has_non_korean_cjk(answer)
            factual_proxy = proxy_pass(
                gold_recall,
                evidence_recall,
                gold_phrase_ratio,
                evidence_phrase_ratio,
                refusal,
            )

            detail_rows.append(
                {
                    "retriever": label,
                    "question_id": row.get("question_id", ""),
                    "doc_id": row.get("doc_id", ""),
                    "question_type": row.get("question_type", ""),
                    "difficulty": row.get("difficulty", ""),
                    "question": row.get("question", ""),
                    "gold_answer": gold_answer,
                    "model_answer": answer,
                    "retrieved_chunk_ids": row.get("retrieved_chunk_ids", ""),
                    "top1_chunk_id": row.get("retrieved_chunk_ids", "").split("|")[0],
                    "gold_token_recall": f"{gold_recall:.3f}",
                    "evidence_token_recall": f"{evidence_recall:.3f}",
                    "gold_phrase_hit_ratio": f"{gold_phrase_ratio:.3f}",
                    "evidence_phrase_hit_ratio": f"{evidence_phrase_ratio:.3f}",
                    "factual_proxy_pass": int(factual_proxy),
                    "refusal_flag": int(refusal),
                    "meta_reasoning_flag": int(meta_reasoning),
                    "non_korean_cjk_flag": int(non_korean_cjk),
                    "korean_char_ratio": f"{korean_ratio:.3f}",
                    "format_proxy_pass": int(
                        (not meta_reasoning)
                        and (not non_korean_cjk)
                        and korean_ratio >= 0.50
                    ),
                    "latency_sec": row.get("latency_sec", ""),
                    "status": row.get("status", ""),
                    "error": row.get("error", ""),
                }
            )

    return detail_rows


def summarize(detail_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in detail_rows:
        grouped[str(row["retriever"])].append(row)

    summary_rows: list[dict[str, object]] = []
    for retriever, rows in grouped.items():
        total = len(rows)
        factual_passes = sum(int(row["factual_proxy_pass"]) for row in rows)
        format_passes = sum(int(row["format_proxy_pass"]) for row in rows)
        meta_flags = sum(int(row["meta_reasoning_flag"]) for row in rows)
        non_korean_cjk_flags = sum(int(row["non_korean_cjk_flag"]) for row in rows)
        refusal_flags = sum(int(row["refusal_flag"]) for row in rows)
        avg_gold_recall = sum(float(row["gold_token_recall"]) for row in rows) / max(total, 1)
        avg_evidence_recall = sum(float(row["evidence_token_recall"]) for row in rows) / max(total, 1)
        avg_korean_ratio = sum(float(row["korean_char_ratio"]) for row in rows) / max(total, 1)
        latencies = [
            float(row["latency_sec"])
            for row in rows
            if str(row.get("latency_sec", "")).strip()
        ]
        avg_latency = sum(latencies) / max(len(latencies), 1)

        summary_rows.append(
            {
                "retriever": retriever,
                "questions": total,
                "factual_proxy_pass_count": factual_passes,
                "factual_proxy_pass_rate": f"{factual_passes / max(total, 1):.3f}",
                "format_proxy_pass_count": format_passes,
                "format_proxy_pass_rate": f"{format_passes / max(total, 1):.3f}",
                "meta_reasoning_count": meta_flags,
                "non_korean_cjk_count": non_korean_cjk_flags,
                "refusal_count": refusal_flags,
                "avg_gold_token_recall": f"{avg_gold_recall:.3f}",
                "avg_evidence_token_recall": f"{avg_evidence_recall:.3f}",
                "avg_korean_char_ratio": f"{avg_korean_ratio:.3f}",
                "avg_latency_sec": f"{avg_latency:.3f}",
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
        help="Answer run as label=path. Can be passed multiple times.",
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
        "gold_answer",
        "model_answer",
        "retrieved_chunk_ids",
        "top1_chunk_id",
        "gold_token_recall",
        "evidence_token_recall",
        "gold_phrase_hit_ratio",
        "evidence_phrase_hit_ratio",
        "factual_proxy_pass",
        "refusal_flag",
        "meta_reasoning_flag",
        "non_korean_cjk_flag",
        "korean_char_ratio",
        "format_proxy_pass",
        "latency_sec",
        "status",
        "error",
    ]
    summary_fields = [
        "retriever",
        "questions",
        "factual_proxy_pass_count",
        "factual_proxy_pass_rate",
        "format_proxy_pass_count",
        "format_proxy_pass_rate",
        "meta_reasoning_count",
        "non_korean_cjk_count",
        "refusal_count",
        "avg_gold_token_recall",
        "avg_evidence_token_recall",
        "avg_korean_char_ratio",
        "avg_latency_sec",
    ]

    write_csv(args.detail_output, detail_rows, detail_fields)
    write_csv(args.output, summary_rows, summary_fields)

    print(f"[DONE] detail saved: {args.detail_output}")
    print(f"[DONE] summary saved: {args.output}")
    for row in summary_rows:
        print(
            "[SUMMARY] "
            f"{row['retriever']} factual={row['factual_proxy_pass_count']}/{row['questions']} "
            f"format={row['format_proxy_pass_count']}/{row['questions']} "
            f"meta={row['meta_reasoning_count']} "
            f"avg_latency={row['avg_latency_sec']}"
        )


if __name__ == "__main__":
    main()
