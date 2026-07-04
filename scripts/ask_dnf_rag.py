from __future__ import annotations

import argparse
import os
import time

import run_rag_local_llm_eval as rag


def build_demo_row(question: str, doc_id: str) -> dict[str, str]:
    return {
        "question_id": "DEMO",
        "doc_id": doc_id,
        "question_type": "demo",
        "difficulty": "demo",
        "question": question,
        "gold_answer": "",
        "evidence": "",
        "expected_behavior": "answer_from_retrieved_context",
    }


def print_retrieved_chunks(results: list[tuple[rag.Chunk, float]]) -> None:
    if not results:
        print("\n[검색 근거]")
        print("- 검색된 근거가 없습니다.")
        return

    print("\n[검색 근거]")
    for rank, (chunk, score) in enumerate(results, start=1):
        preview = " ".join(chunk.text.split())
        if len(preview) > 180:
            preview = f"{preview[:180]}..."
        print(
            f"- {rank}. {chunk.chunk_id} | {chunk.doc_id} | "
            f"score={score:.3f} | {chunk.title}"
        )
        print(f"  {preview}")


def print_structured_records(records: list[dict[str, object]]) -> None:
    if not records:
        return

    print("\n[구조화 데이터]")
    for record in records:
        print(
            "- {item_name} | price={price_text} | limit={purchase_limit_text} | "
            "carryover={carryover_text}".format(**record)
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ask one DNF document-based RAG question from the local workspace."
    )
    parser.add_argument("question", help="질문 문장")
    parser.add_argument("--doc-id", default="", help="특정 문서로 검색 범위를 제한합니다. 예: DOC-01")
    parser.add_argument("--model", default=os.getenv("OLLAMA_MODEL", "qwen3:4b"))
    parser.add_argument("--endpoint", default=os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/chat"))
    parser.add_argument("--retriever", choices=["bm25", "bge-m3", "hybrid"], default="bm25")
    parser.add_argument("--embedding-model", default=rag.DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--embedding-batch-size", type=int, default=8)
    parser.add_argument("--embedding-max-length", type=int, default=8192)
    parser.add_argument("--embedding-min-score", type=float, default=0.0)
    parser.add_argument("--bge-use-fp16", action="store_true")
    parser.add_argument("--hybrid-alpha", type=float, default=0.5)
    parser.add_argument("--window-lines", type=int, default=15)
    parser.add_argument("--stride", type=int, default=3)
    parser.add_argument("--chunk-max-chars", type=int, default=1600)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-score", type=float, default=2.0)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--num-predict", type=int, default=220)
    parser.add_argument("--num-ctx", type=int, default=0)
    parser.add_argument("--use-structured-data", action="store_true")
    parser.add_argument("--disable-thinking", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="모델 호출 없이 검색 근거만 확인합니다.")
    parser.add_argument(
        "--no-safety-gate",
        action="store_true",
        help="데모용 안전 게이트를 끕니다. 기본값은 안전 게이트 사용입니다.",
    )
    args = parser.parse_args()

    row = build_demo_row(args.question, args.doc_id)
    started = time.perf_counter()

    blocked_category, blocked_reason = ("", "")
    if not args.no_safety_gate:
        blocked_category, blocked_reason = rag.get_safety_block(args.question)

    print("[질문]")
    print(args.question)
    print(
        "\n[설정] "
        f"retriever={args.retriever}, model={args.model}, top_k={args.top_k}, "
        f"doc_id={args.doc_id or 'ALL'}, structured={args.use_structured_data}"
    )

    if blocked_reason:
        print("\n[안전 게이트]")
        print(f"- blocked_category={blocked_category}")
        print(f"- blocked_reason={blocked_reason}")
        print("\n[답변]")
        print(rag.SAFE_REFUSAL)
        return

    chunks = rag.build_chunks(args.window_lines, args.stride, args.chunk_max_chars)
    if args.doc_id:
        chunks = [chunk for chunk in chunks if chunk.doc_id == args.doc_id]

    idf = rag.compute_idf(chunks)
    embedding_runner = None
    chunk_vectors: list[list[float]] = []

    if args.retriever in {"bge-m3", "hybrid"}:
        embedding_runner = rag.load_bge_m3_model(args.embedding_model, args.bge_use_fp16)
        chunk_vectors = rag.load_or_build_chunk_embeddings(
            chunks,
            embedding_runner,
            args.embedding_model,
            args.embedding_batch_size,
            args.embedding_max_length,
        )

    results = rag.retrieve_chunks(
        query=args.question,
        chunks=chunks,
        idf=idf,
        top_k=args.top_k,
        min_score=args.min_score,
        doc_filter=args.doc_id,
        retriever=args.retriever,
        chunk_vectors=chunk_vectors,
        embedding_runner=embedding_runner,
        embedding_min_score=args.embedding_min_score,
        embedding_batch_size=args.embedding_batch_size,
        embedding_max_length=args.embedding_max_length,
        hybrid_alpha=args.hybrid_alpha,
    )

    retrieved_context = rag.format_context(results)
    structured_records = []
    structured_context = ""
    if args.use_structured_data:
        structured_records = rag.find_structured_shop_records(
            row,
            rag.read_structured_shop_records(),
        )
        structured_context = rag.format_structured_context(structured_records)

    context = rag.combine_context(structured_context, retrieved_context)
    print_retrieved_chunks(results)
    print_structured_records(structured_records)

    if args.dry_run:
        print("\n[답변]")
        print("dry-run 모드라 모델 호출은 생략했습니다.")
        print(f"\n[DONE] latency={time.perf_counter() - started:.3f}s")
        return

    answer = rag.call_ollama(
        endpoint=args.endpoint,
        model=args.model,
        row=row,
        context=context,
        timeout=args.timeout,
        num_predict=args.num_predict,
        num_ctx=args.num_ctx,
        disable_thinking=args.disable_thinking,
        structured_source_relation=True,
        structured_completeness_rules=True,
    )

    print("\n[답변]")
    print(answer or "모델이 빈 답변을 반환했습니다.")
    print(f"\n[DONE] latency={time.perf_counter() - started:.3f}s")


if __name__ == "__main__":
    main()
