# DeepEval faithfulness manual review

작성일: 2026-07-01
대상 실행: `eval/deepeval_rag_v2026_06_hybrid_structured_faithfulness_judge.csv`
연계 문서: `report/deepeval_adapter_notes.md`

## 목적

DeepEval faithfulness judge는 2026-06 structured RAG 답변 20문항 중 7문항을 fail로 판정했다. 이 문서는 그 7건을 사람이 다시 읽어, 실제 생성 오류와 judge 오류를 분리한다.

수동 리뷰 산출물:

- `eval/deepeval_rag_v2026_06_faithfulness_manual_review.csv`

## 요약

| 분류 | 문항 | 건수 | 해석 |
|---|---|---:|---|
| confirmed model error | `Q001` | 1 | 답변이 근거와 충돌하거나 잘못된 관계를 생성 |
| partial model error | `Q012` | 1 | 핵심 수치는 맞지만 expected behavior 일부 누락 |
| judge false positive / overstrict | `Q002`, `Q011`, `Q015`, `Q016`, `Q020` | 5 | 답변은 근거/정답과 맞지만 judge가 오판 |

DeepEval 원점수만 보면 pass 13/20, fail 7/20이다. 수동 리뷰 기준으로는 명확한 생성 오류 1건, 부분 오류 1건, judge 오류 5건으로 보는 것이 더 타당하다. 따라서 DeepEval 결과는 최종 정답 판정자가 아니라 manual review queue를 정렬하는 보조 신호로 사용해야 한다.

## 케이스별 판정

| QID | DeepEval | Manual verdict | 판정 |
|---|---:|---|---|
| `Q001` | 0.333 | confirmed model error | 전리품 상점 신규 물품의 가격/구매 제한 관계를 잘못 묶었다. 실제 근거는 검은 재앙 1개 상자 가격 `초월의 의지 50개`, 구매 제한 `계정당 주 10회`인데, 답변은 가격이 조정되지 않았다고 말하고 50→25 조정을 구매 제한처럼 설명했다. |
| `Q002` | 0.500 | judge false positive | 답변은 보이드 소울 2개 가격이 `초월의 의지 50개 → 25개`로 조정된다고 정확히 답했다. judge가 화살표 표현을 잘못 해석한 것으로 보인다. |
| `Q011` | 0.000 | judge false positive | 답변은 타이드 바운드 쿨타임 `20초 → 18초`를 정확히 답했다. judge는 별도 문항인 질풍 옵션의 `12초 → 9초` 근거와 혼동했다. |
| `Q012` | 0.000 | partial model error with bad judge reason | 답변은 질풍 옵션 기본 쿨타임 `12초 → 9초`는 맞췄지만, expected behavior의 `공격력 11.5% 감소 조건 유지`를 빠뜨렸다. 단, judge reason은 12→9 근거가 없다고 말해 잘못됐다. |
| `Q015` | 0.000 | judge self-consistency error | 답변은 몬스터명 변경 `로즈베리론 → 청면수라 로즈베리론`, `지젤로건 → GB-1 햅스`를 정확히 답했다. judge reason은 full alignment를 말하면서 score만 0.000을 줬다. |
| `Q016` | 0.000 | judge false positive | 답변은 타이드 피어서 충전 기능 삭제와 앞 방향키 입력 시 전방 이동 시전 변경을 모두 맞췄다. judge가 앞 방향키 근거를 놓쳤다. |
| `Q020` | 0.000 | judge overstrict / rubric ambiguous | 답변은 랜딩 문서의 업데이트 날짜와 구성 항목을 gold answer와 동일하게 답했다. judge는 `주요 구성요소`라는 label을 과하게 문제 삼았다. 질문 자체가 주요 구성요소를 요구하므로 오판에 가깝다. |

## 개선 우선순위

1. `Q001` table/value binding 개선
   - 전리품 상점처럼 item, price, purchase limit가 붙은 행은 plain chunk만으로 모델이 열 관계를 섞을 수 있다.
   - 다음 구현 후보는 2026-06 snapshot용 shop item structured record를 보강하거나, 표/목록형 근거를 key-value 형태로 prompt 앞에 붙이는 것이다.

2. `Q012` structured `unchanged` 필드 답변 반영
   - 현재 structured change record에는 `unchanged: 공격력 11.5% 감소`가 들어 있다.
   - 답변 prompt가 before/after만 말하고 unchanged 조건을 생략하지 않도록 규칙을 추가해야 한다.

3. DeepEval judge calibration
   - 긴 retrieval context에서 judge가 문항 간 유사 chunk를 혼동했다.
   - 다음 judge 실행은 전체 context 대신 question-specific compact evidence, structured context, top evidence chunk만 넣는 실험이 필요하다.
   - judge reason과 score가 모순될 때는 자동 fail로 확정하지 말고 `judge_self_consistency_error`로 분리한다.

## 다음 단계

추천 진행은 `Q001`과 `Q012`를 먼저 고치는 것이다. 이 둘은 실제 RAG 답변 품질과 연결된다. 나머지 5건은 answer generation보다 judge calibration 문제에 가깝기 때문에, 생성 파이프라인 수정 전에 judge context 축약 실험으로 따로 다루는 편이 낫다.
