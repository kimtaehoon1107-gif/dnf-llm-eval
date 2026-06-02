# 구조화 데이터 및 Safety Gate 개선 기록

작성일: 2026-05-29

## 1. 처리한 개선

이번 개선에서는 두 가지를 처리했다.

1. 표형 상점 데이터를 JSON record로 변환
2. safety gate를 단순 키워드 차단에서 카테고리 기반 기록 방식으로 개선

## 2. 표형 데이터 구조화

RAG 적용 후에도 상점 표처럼 줄 단위로 풀린 데이터에서는 가격, 구매 제한, 이월 조건이 인접 항목과 섞이는 문제가 남았다. 이를 줄이기 위해 `scripts/build_structured_shop_data.py`를 추가했다.

생성 파일:

```text
data/structured/shop_items.json
```

현재 추출 대상:

- DOC-01: 5/28 정기점검 업데이트의 켈돈 자비 상점 아이템 5개
- DOC-02: 5/20 퍼스트 서버 업데이트의 켈돈 자비 상점 아이템 5개

주요 필드:

| 필드 | 의미 |
|---|---|
| record_id | 구조화 record ID |
| doc_id | 원본 문서 ID |
| item_name | 아이템명 |
| price_text | 원문 가격 |
| price_quantity | 가격 수량 |
| purchase_limit_text | 원문 구매 제한 |
| purchase_limit_count | 제한 횟수 |
| carryover_text | 구매 횟수 이월 조건 |

## 3. RAG 연결 방식

`scripts/run_rag_local_llm_eval.py`에 `--use-structured-data` 옵션을 추가했다.

동작 방식:

```text
질문
→ safety gate
→ BM25 chunk 검색
→ 아이템명 기반 structured record 검색
→ structured context + retrieved context 결합
→ LLM 답변
```

검증 명령:

```powershell
python scripts\run_rag_local_llm_eval.py `
  --questions questions\benchmark_questions.csv `
  --output eval\rag_structured_retrieval_sample.csv `
  --model qwen3:4b `
  --limit 4 `
  --restrict-to-question-doc `
  --use-structured-data `
  --dry-run
```

검증 결과:

| 질문 | 연결된 structured record | 확인된 정보 |
|---|---|---|
| Q002 | DOC-01-SHOP-01 | 태초 광휘의 의지, 광휘의 잔영 790개, 계정당 1회 |
| Q003 | DOC-01-SHOP-02 | 태초 소울 1개 상자, 광휘의 잔영 120개, 계정당 월 4회, 이월 |
| Q004 | DOC-01-SHOP-03 | 에픽 소울 1개 상자, 광휘의 잔영 8개, 계정당 월 15회, 이월 |

추가로 실제 모델 답변 샘플도 4문항만 실행했다.

```text
eval/rag_structured_answers_sample.csv
```

결과:

| 질문 | 결과 요약 | latency |
|---|---|---:|
| Q001 | 주요 재화 질문에서 아이템 목록까지 함께 답해 추가 점검 필요 | 46.54초 |
| Q002 | 태초 광휘의 의지 가격 790개, 계정당 1회로 정확히 답변 | 15.13초 |
| Q003 | 태초 소울 1개 상자 가격 120개, 계정당 월 4회로 정확히 답변 | 22.07초 |
| Q004 | 에픽 소울 1개 상자 이월 조건을 최대 15회까지 다음달 이월로 정확히 답변 | 13.90초 |

즉, 구조화 데이터는 가격/구매 제한/이월 질문에서 효과가 있었지만, 일반 보상 질문에서는 답변 범위를 더 좁히는 후처리 또는 프롬프트 개선이 남아 있다.

## 4. Safety Gate 카테고리 개선

기존 safety gate는 차단 키워드만 `blocked_reason`에 남겼다. 개선 후에는 다음 두 컬럼을 기록한다.

| 컬럼 | 의미 |
|---|---|
| blocked_category | 공격 유형 |
| blocked_reason | 실제로 매칭된 차단 키워드 |

예시 카테고리:

- prompt_injection
- prompt_leakage
- jailbreak
- exploit_request
- automation_abuse
- fake_evidence
- hallucination_induction

재생성한 결과 파일:

```text
eval/local_llm_adversarial_answers_safety_gate.csv
eval/rag_local_llm_adversarial_answers_safety_gate.csv
```

두 파일 모두 공격성 질문 10개를 10개 모두 사전 차단했다.

## 5. 남은 작업

다음 단계는 `RAG only`와 `RAG + structured data`를 Q002~Q004 중심으로 같은 루브릭으로 채점해 정확성, 근거성, 완전성 점수 차이를 비교하는 것이다.
