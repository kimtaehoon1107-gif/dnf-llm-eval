# BGE-M3 Retrieval Smoke Test

작성일: 2026-06-01

## 1. 목적

BGE-M3 embedding retriever가 로컬 환경에서 정상 동작하는지, 그리고 BM25 heuristic과 다른 ranking을 만드는지 빠르게 확인했다.

이 smoke test는 최종 성능 평가가 아니라 기능 확인용이다. 최종 판단은 `report/retriever_comparison_report.md`의 22문항 비교 결과를 기준으로 한다.

## 2. 실행 조건

| 항목 | 값 |
|---|---|
| 질문 수 | DOC-01 관련 2문항 |
| 비교 | BM25 heuristic, BGE-M3 |
| 출력 | `eval/rag_bm25_retriever_smoke.csv`, `eval/rag_bge_m3_retriever_smoke.csv` |
| 목적 | 검색기 동작 확인 및 top chunk 차이 확인 |

BGE-M3 첫 실행은 Hugging Face 모델 다운로드와 chunk embedding 생성 때문에 시간이 오래 걸릴 수 있다. 이후 실행은 cache를 사용하므로 훨씬 빠르다.

## 3. 실행 명령

BM25 heuristic:

```powershell
python scripts\run_rag_local_llm_eval.py `
  --questions questions\benchmark_questions.csv `
  --output eval\rag_bm25_retriever_smoke.csv `
  --model qwen3:4b `
  --retriever bm25 `
  --dry-run `
  --limit 2
```

BGE-M3:

```powershell
python scripts\run_rag_local_llm_eval.py `
  --questions questions\benchmark_questions.csv `
  --output eval\rag_bge_m3_retriever_smoke.csv `
  --model qwen3:4b `
  --retriever bge-m3 `
  --dry-run `
  --limit 2
```

## 4. 관찰

Q002처럼 상점표 내부의 가격과 구매 제한을 묻는 질문에서 BGE-M3는 BM25 heuristic보다 표 내부의 직접 관련 chunk를 더 높은 순위로 올렸다. 이 결과는 embedding 검색이 짧은 유저 질문과 문서 내부 의미를 연결하는 데 도움이 될 수 있음을 보여준다.

다만 smoke test는 2문항만 사용했기 때문에 최종 결론으로 사용하지 않는다. 최종 검색기 선택은 22문항 retrieval 비교에서 BGE-M3가 BM25 heuristic보다 top-1 evidence hit가 높았다는 결과를 기준으로 한다.

## 5. 결론

BGE-M3는 로컬 환경에서 정상 동작했고, BM25 heuristic과 다른 ranking을 생성했다. 이후 전체 benchmark 비교에서 BGE-M3가 더 높은 top-1 evidence hit를 보여 최종 검색기로 선택했다.
