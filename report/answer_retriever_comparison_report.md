# Answer Quality Comparison: BM25 vs BGE-M3

작성일: 2026-06-01

## 1. 목적

이 보고서는 같은 22개 benchmark 질문에 대해 검색기를 바꿨을 때 실제 로컬 LLM 답변 품질이 어떻게 달라지는지 비교한다.

최종 제출용 검색기 비교군은 `BM25 heuristic + qwen3:4b`와 `BGE-M3 + qwen3:4b`로 정리한다. 여기서 BM25는 순수 BM25가 아니라 phrase/coverage/intent bonus를 더한 BM25 기반 검색기다. 이 문서는 검색기 비교용 중간 실험이며, 최종 생성 모델과 structured data의 변수별 효과는 `report/ablation_study_report.md`, `report/heldout_factual_ablation_v1.md`, `report/structured_record_probe_v1.md`를 기준으로 해석한다.

## 2. 평가 방식

| 지표 | 의미 |
|---|---|
| Factual proxy | 기준 정답과 evidence의 핵심 token이 답변에 포함되는지 |
| Format proxy | 영어 추론, 메타 발화, 비한국어 문자가 없이 한국어 답변 형식으로 출력되는지 |
| Meta reasoning | `Okay`, `let's`, `the user is asking` 같은 사고 과정 노출 여부 |
| Avg latency | 질문당 평균 응답 시간 |

자동 proxy는 빠른 비교용 지표다. 최종 판단에는 `eval/representative_manual_scoring.csv`의 수동 루브릭 평가를 함께 사용한다.

## 3. 실행 명령

BM25 heuristic:

```powershell
python scripts\run_rag_local_llm_eval.py `
  --questions questions\benchmark_questions.csv `
  --output eval\answer_compare_bm25.csv `
  --model qwen3:4b `
  --restrict-to-question-doc `
  --retriever bm25 `
  --disable-thinking `
  --num-predict 220
```

BGE-M3:

```powershell
python scripts\run_rag_local_llm_eval.py `
  --questions questions\benchmark_questions.csv `
  --output eval\answer_compare_bge_m3.csv `
  --model qwen3:4b `
  --restrict-to-question-doc `
  --retriever bge-m3 `
  --disable-thinking `
  --num-predict 220
```

요약 생성:

```powershell
python scripts\score_answer_runs.py `
  --run bm25=eval\answer_compare_bm25.csv `
  --run bge-m3=eval\answer_compare_bge_m3.csv `
  --output eval\answer_compare_summary.csv `
  --detail-output eval\answer_compare_detail.csv
```

## 4. 결과 요약

| 설정 | Factual proxy | Format proxy | Meta reasoning | Avg latency |
|---|---:|---:|---:|---:|
| BM25 heuristic + `qwen3:4b` | 17 / 22 | 0 / 22 | 22 | 8.964s |
| BGE-M3 + `qwen3:4b` | 19 / 22 | 0 / 22 | 21 | 9.063s |

BGE-M3는 factual proxy 기준으로 BM25보다 좋았다. 검색 단계에서 top-1 evidence hit가 개선된 효과가 답변 품질에도 일부 반영된 것으로 볼 수 있다.

하지만 두 설정 모두 format proxy는 0/22였다. 즉, 검색기가 좋아져도 `qwen3:4b`가 영어 추론 과정과 메타 발화를 노출하는 문제는 해결되지 않았다.

## 5. 생성 설정 ablation과의 연결

검색기 비교 이후 병목은 retrieval이 아니라 generation format으로 판단했다. 그래서 추가 실험에서는 검색기를 BGE-M3로 고정하고, 생성 모델과 프롬프트 설정을 단계적으로 바꿨다.

| 설정 | Factual proxy | Format proxy | Meta reasoning | Avg latency |
|---|---:|---:|---:|---:|
| BGE-M3 + `qwen3:4b` | 17 / 22 | 9 / 22 | 13 | 11.635s |
| BGE-M3 + `qwen3:4b-instruct-2507` | 18 / 22 | 22 / 22 | 0 | 4.625s |

가장 큰 개선은 모델만 instruct variant로 바꿨을 때 발생했다. Format proxy가 9/22에서 22/22로 개선됐고, meta reasoning 출력은 13건에서 0건으로 줄었다. Structured data는 표형 정보 보완을 위한 별도 구성 요소이며, factual proxy 변화는 token 기반 자동 지표의 false negative 가능성을 함께 고려해 해석한다.

## 6. 오류 분석

### Q002: 표형 데이터 혼입

`태초 광휘의 의지`는 `광휘의 잔영 790개`, `계정당 1회`가 정답이다. 최종 조합에서도 가격과 구매 제한은 맞혔지만, 인접 상품인 `태초 소울 1개 상자`의 월 제한 조건이 섞이는 문제가 남았다.

이는 retriever 문제가 아니라 generator가 표의 인접 행을 혼합한 문제에 가깝다. 해결 방향은 structured record 우선 규칙, item-name exact match, answer template 적용이다.

### Q016: 자동 proxy 오판

Q016은 답변 내용상 `라이브 서버 HP 90`, `성화 작열 감소 HP 30`으로 맞았지만 token 기반 factual proxy에서는 실패로 잡혔다. 이 사례는 자동 proxy만으로 최종 품질을 판단하면 안 되고, 대표 문항 수동 채점이 필요하다는 근거다.

## 7. 결론

답변 품질 비교 결과, BGE-M3는 BM25 heuristic보다 사실성 proxy를 개선했다. 그러나 검색 개선만으로는 답변 형식 문제가 해결되지 않았다.

최종 결론은 다음과 같다.

```text
Retriever: BGE-M3
Context 보완: structured shop data
Generator: qwen3:4b-instruct-2507-q4_K_M
Prompt: disable-thinking + concise Korean answer format
```

이 조합이 현재 포트폴리오 제출용으로 가장 일관된 결과를 보인다.
