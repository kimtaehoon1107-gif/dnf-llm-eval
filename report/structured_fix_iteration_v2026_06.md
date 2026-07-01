# 2026-06 structured fix iteration

작성일: 2026-07-01
연계 문서: `report/deepeval_faithfulness_manual_review.md`

## 목적

DeepEval faithfulness fail 7건을 수동 리뷰한 뒤, 실제 생성 품질 개선 대상인 `Q001`, `Q012`를 먼저 수정했다.

수정 목표:

- `Q001`: 전리품 상점 표에서 신규 물품의 가격과 구매 제한을 다른 조정 항목과 섞지 않기
- `Q012`: structured change record의 `unchanged` 조건을 답변에 포함하기

## 수정 내용

1. Snapshot 전용 shop structured data 추가
   - `data/snapshots/2026-06-official-updates/structured/shop_items.json`
   - `DNF-2927810-SHOP-01`: 검은 재앙 1개 상자(초월의 의지), 가격 `초월의 의지 50개`, 구매 제한 `계정당 주 10회`
   - `DNF-2927810-SHOP-02`: 보이드 소울 2개(초월의 의지), 가격 `초월의 의지 50개 → 초월의 의지 25개`

2. RAG runner 구조화 데이터 로딩 개선
   - snapshot 경로에 `structured/shop_items.json`이 있으면 기존 `data/structured/shop_items.json`보다 우선 사용한다.
   - shop record의 `match_terms`를 지원해, 질문에 item name이 직접 없더라도 `전리품 상점`, `신규 물품`, `새로 추가`, `가격`, `구매 제한` 신호로 관련 record를 붙일 수 있게 했다.

3. Prompt 규칙 강화
   - 구조화 근거가 있으면 `item_name`, `price`, `purchase_limit`, `before`, `after`, `unchanged` 관계를 일반 chunk보다 우선한다.
   - `patch_change` 구조화 근거의 `unchanged`가 있으면 질문이 특정 field 변경만 묻더라도 before/after와 함께 unchanged 조건도 포함하도록 했다.
   - patch_change formatted context에 `answer_requirement`를 추가했다.

4. Regression 질문셋 추가
   - `questions/regression_questions_v2026_06_structured_fix.csv`
   - `Q001`, `Q012` 2문항만 포함해 빠른 재검증이 가능하게 했다.

## 검증 결과

실행:

```powershell
python scripts\run_rag_local_llm_eval.py `
  --questions questions\benchmark_questions_v2026_06.csv `
  --question-set-id benchmark_questions_v2026_06 `
  --doc-dir data\snapshots\2026-06-official-updates\processed_md `
  --metadata data\snapshots\2026-06-official-updates\metadata.csv `
  --retriever hybrid `
  --use-structured-data `
  --model qwen3:4b-instruct-2507-q4_K_M `
  --disable-thinking `
  --num-predict 512 `
  --num-ctx 8192 `
  --output eval\rag_v2026_06_hybrid_structured_fix_instruct_answers.csv
```

비교:

| run | factual proxy | format proxy | meta reasoning | avg latency |
|---|---:|---:|---:|---:|
| before | 16 / 20 | 20 / 20 | 0 | 4.273s |
| after | 17 / 20 | 20 / 20 | 0 | 4.178s |

Target regression:

| QID | 결과 |
|---|---|
| `Q001` | `검은 재앙 1개 상자(초월의 의지)` 가격 `초월의 의지 50개`, 구매 제한 `계정당 주 10회`로 정상 답변 |
| `Q012` | `12초 → 9초` 변경과 `공격력 11.5% 감소 조건 유지`를 함께 답변 |

부작용 확인:

- factual proxy가 떨어진 문항은 없었다.
- `Q013`은 structured `unchanged` 포함 규칙 덕분에 proxy 기준으로 추가 개선됐다.
- 남은 proxy fail은 `Q003`, `Q014`, `Q018` 3건이다. 답변이 매우 짧아 phrase proxy가 낮게 잡힌 성격이 있어 다음 단계에서 사람이 다시 확인해야 한다.

## 산출물

- `eval/rag_v2026_06_hybrid_structured_fix_instruct_answers.csv`
- `eval/rag_v2026_06_hybrid_structured_fix_instruct_answers.manifest.json`
- `eval/v2026_06_structured_fix_answer_compare_summary.csv`
- `eval/v2026_06_structured_fix_answer_compare_detail.csv`
- `eval/rag_v2026_06_structured_fix_regression_answers.csv`
- `eval/rag_v2026_06_structured_fix_regression_answers.manifest.json`
- `eval/v2026_06_structured_fix_regression_answer_summary.csv`
- `eval/v2026_06_structured_fix_regression_answer_detail.csv`

## 다음 단계

1. 남은 proxy fail `Q003`, `Q014`, `Q018`을 수동 리뷰한다.
2. 답변이 사실상 맞지만 너무 짧아 proxy가 실패한 경우, answer proxy/rubric을 보정한다.
3. 실제 누락이면 질문 유형별 answer completeness rule을 추가한다.
