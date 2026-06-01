# Retriever Comparison Report

작성일: 2026-06-01

## 1. 목적

이 보고서는 던전앤파이터 업데이트 문서 기반 benchmark에서 `BM25 heuristic`과 `BGE-M3` 검색기가 gold evidence를 얼마나 잘 찾는지 비교한 결과를 정리한다.

최종 제출용 스토리에서는 비교군을 단순하게 유지하기 위해 `BM25 heuristic`을 키워드 기반 baseline으로, `BGE-M3`를 최종 검색 후보로 둔다. RAG 시스템의 핵심 개선 여부를 보여주기에는 두 비교군만으로도 충분하며, 추가 조합은 후속 실험 후보로 남긴다.

## 2. 비교 대상

| Retriever | 역할 | 설명 |
|---|---|---|
| BM25 heuristic | Baseline | BM25 점수에 phrase/coverage/intent bonus를 더한 키워드 중심 검색 방식 |
| BGE-M3 | Final candidate | 한국어 포함 다국어 dense embedding 검색 모델 |

공통 조건은 다음과 같다.

| 항목 | 설정 |
|---|---|
| 질문 세트 | `questions/benchmark_questions.csv` 22문항 |
| 문서 제한 | `--restrict-to-question-doc` 사용 |
| 검색 개수 | top-k 8 |
| 평가 방식 | dry-run, 답변 생성 없음 |

`--restrict-to-question-doc`는 실제 서비스 옵션이 아니라 평가용 ablation이다. 질문의 정답 문서 안에서만 검색하게 하여 검색 ranking 자체를 더 깨끗하게 비교하기 위해 사용했다.

## 3. 실행 명령

BM25 heuristic:

```powershell
python scripts\run_rag_local_llm_eval.py `
  --questions questions\benchmark_questions.csv `
  --output eval\retrieval_compare_bm25.csv `
  --model qwen3:4b `
  --restrict-to-question-doc `
  --retriever bm25 `
  --dry-run
```

BGE-M3:

```powershell
python scripts\run_rag_local_llm_eval.py `
  --questions questions\benchmark_questions.csv `
  --output eval\retrieval_compare_bge_m3.csv `
  --model qwen3:4b `
  --restrict-to-question-doc `
  --retriever bge-m3 `
  --dry-run
```

비교 요약 생성:

```powershell
python scripts\score_retrieval_runs.py `
  --run bm25=eval\retrieval_compare_bm25.csv `
  --run bge-m3=eval\retrieval_compare_bge_m3.csv `
  --output eval\retrieval_compare_summary.csv `
  --detail-output eval\retrieval_compare_detail.csv
```

## 4. 결과 요약

| Retriever | Top-8 evidence hit | Top-1 evidence hit | Avg token recall | 해석 |
|---|---:|---:|---:|---|
| BM25 heuristic | 22 / 22 | 19 / 22 | 0.994 | top-k 안에는 근거가 들어오지만 일부 질문에서 1순위가 흔들림 |
| BGE-M3 | 22 / 22 | 21 / 22 | 1.000 | top-1 기준 더 안정적이며 최종 검색기로 선택 |

두 검색기 모두 top-8 안에는 모든 문항의 gold evidence를 포함했다. 즉, RAG가 baseline보다 크게 개선된 이유는 top-k context 안에 필요한 공식 문서 근거가 충분히 들어갔기 때문이다.

차이는 top-1 ranking에서 나타났다. BGE-M3는 22문항 중 21문항에서 top-1 evidence hit를 기록했고, BM25 heuristic은 19문항이었다. 따라서 최종 실험에서는 BGE-M3를 기본 검색기로 사용했다.

## 5. 대표 관찰

### Q002: 태초 광휘의 의지 가격/구매 제한

| Retriever | Top chunk | 해석 |
|---|---|---|
| BM25 heuristic | DOC-01-C0005 | 관련 문서 초반 chunk를 우선 회수 |
| BGE-M3 | DOC-01-C0009 | 가격과 구매 제한이 있는 표 내부 chunk를 1순위로 회수 |

BGE-M3는 짧은 질문과 표 내부 의미를 더 잘 연결했다. 다만 이후 답변 생성 단계에서 인접 행의 조건이 섞이는 오류가 남았기 때문에, 표형 데이터는 별도 구조화가 필요하다는 결론으로 이어졌다.

### Q007: 브레이커 덱 브레이커 스킬

Q007은 스킬 설명이 긴 문서 안에 흩어져 있어 top-1 하나만으로는 충분하지 않았다. 두 검색기 모두 top-8 안에는 관련 근거를 포함했으므로, 이 유형은 검색기 자체보다 chunk 크기, section chunking, reranker 개선 후보로 보는 것이 타당하다.

## 6. 결론

BGE-M3는 BM25 heuristic보다 top-1 근거 회수 성능이 높았고, 던파처럼 한국어 게임 문서와 짧은 유저 질문을 연결하는 작업에 더 적합했다. 다만 BM25 baseline에는 phrase/coverage/intent bonus가 포함되어 있으므로, 더 엄밀한 비교를 위해서는 순수 BM25 점수를 별도로 산출할 수 있다. 따라서 최종 파이프라인은 다음 구조로 정리한다.

```text
BM25 heuristic = baseline retriever
BGE-M3 = final retriever
structured JSON = 표형 데이터 보완
```

향후에는 BGE-M3 top-k 결과 위에 reranker를 추가해 긴 패치노트 내부의 세부 섹션 순위를 더 정밀하게 조정할 수 있다.
