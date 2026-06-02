# 다음 개선 계획: 표형 데이터 구조화

## 문제

RAG 적용 후 대부분의 긴 문서 탐색 문제는 개선되었지만, 상점/보상 표처럼 줄 단위로 풀린 데이터에서는 여전히 일부 오류가 남았다.

대표 사례:

- `태초 광휘의 의지` 가격과 구매 제한을 검색 근거에 포함했지만 모델이 확인 불가로 답변
- `태초 소울 1개 상자`의 월 구매 제한은 맞췄지만 가격 `광휘의 잔영 120개`를 누락

## 원인

Markdown 본문에서는 원래 표였던 정보가 다음처럼 줄 단위 텍스트로 풀린다.

```text
태초 소울 1개 상자
사용 시 태초 소울 1개를 획득할 수 있습니다.
<구매 가능 횟수>
- 월 4회
남은 구매 횟수는 최대 4회까지 다음달로 이월되어 적용됩니다.
교환불가
광휘의 잔영 120개
계정당 월 4회
```

사람은 이 줄들이 같은 아이템에 속한다는 것을 쉽게 이해하지만, 경량 LLM은 인접 항목의 가격이나 제한을 섞어 해석할 수 있다.

## 개선 방향

상점/보상 표를 별도 구조화 데이터로 추출한다.

예상 구조:

```json
{
  "doc_id": "DOC-01",
  "section": "NPC 상점",
  "item": "태초 소울 1개 상자",
  "description": "사용 시 태초 소울 1개를 획득할 수 있습니다.",
  "price": "광휘의 잔영 120개",
  "limit": "계정당 월 4회",
  "carryover": "남은 구매 횟수는 최대 4회까지 다음달로 이월"
}
```

## 기대 효과

- 가격/구매 제한 질문의 정확도 향상
- 표형 데이터에서 인접 항목 수치 혼동 감소
- RAG 검색 결과를 자연어 chunk와 구조화 record로 함께 제공 가능
- 실제 서비스형 QA에서 데이터 정규화가 왜 필요한지 설명 가능

## 구현 순서

1. DOC-01, DOC-02의 상점/보상 영역에서 아이템 단위 record 추출
2. `data/structured/shop_items.json` 생성
3. 질문에 아이템명이 포함되면 구조화 record를 우선 검색
4. qwen3:4b에 자연어 chunk와 structured context를 함께 제공
5. Q002, Q003, Q004를 재평가
6. RAG only vs RAG + structured data 결과 비교

## 구현 결과

2026-05-29 기준으로 1~4번을 구현했다.

- `scripts/build_structured_shop_data.py`를 추가해 Markdown으로 풀린 NPC 상점 표를 아이템 단위 JSON으로 변환했다.
- `data/structured/shop_items.json`에 DOC-01, DOC-02의 켈돈 자비 상점 아이템 10개를 저장했다.
- 각 record에는 `item_name`, `price_text`, `price_quantity`, `purchase_limit_text`, `purchase_limit_count`, `carryover_text`를 포함했다.
- `scripts/run_rag_local_llm_eval.py`에 `--use-structured-data` 옵션을 추가해 질문에 아이템명과 가격/구매 제한 표현이 포함되면 구조화 record를 검색 근거 앞에 붙이도록 했다.

검증 결과:

```text
Q002 → DOC-01-SHOP-01: 태초 광휘의 의지 / 광휘의 잔영 790개 / 계정당 1회
Q003 → DOC-01-SHOP-02: 태초 소울 1개 상자 / 광휘의 잔영 120개 / 계정당 월 4회 / 다음달 이월
Q004 → DOC-01-SHOP-03: 에픽 소울 1개 상자 / 광휘의 잔영 8개 / 계정당 월 15회 / 다음달 이월
```

검증 산출물은 `eval/rag_structured_retrieval_sample.csv`에 저장했다.

실제 모델 답변 샘플은 `eval/rag_structured_answers_sample.csv`에 저장했다. Q002~Q004는 가격, 구매 제한, 이월 조건을 정확히 답했지만, Q001은 주요 재화 질문에서 관련 아이템 목록까지 함께 답하는 오류가 남았다.

남은 작업은 기존 `RAG only` 결과와 `RAG + structured data` 결과를 같은 루브릭으로 비교 채점하는 것이다.
