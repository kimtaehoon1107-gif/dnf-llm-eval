# DeepEval Faithfulness Fail 6건 — 독립 재검증

작성일: 2026-07-04
원본 판정: `report/deepeval_compact_evidence_calibration_v2026_06.md` (compact top-3 fail 6건을 전부 "judge 오류"로 자체 분류)

## 왜 다시 봤나

원래 문서는 프로젝트를 만든 쪽이 스스로 실패 6건을 전부 "judge의 문제"로 판정했다. 자기 판정이라 편의적 해석 위험이 있다는 점이 이미 `research_overview_master.md` 5장에 한계로 적혀 있었다. 여기서는 그 판정을 보지 않은 상태로 문항·근거·모델 답변·judge reason을 다시 읽고 독립적으로 동의/비동의를 매겼다.

## 재검증 결과

| QID | 원래 판정 | 독립 재검증 | verdict |
|---|---|---|---|
| Q003 | judge 오류 | 애매함 — 모델 답변이 "안개 서약 최대 단계 이후"라는 전제 조건을 명시하지 않은 건 사실. judge가 이를 "모순"으로 부른 건 과하지만, 완전한 judge 오류라고 단정하기도 어렵다 | PLAUSIBLE (약한 동의) |
| Q012 | judge 오류 | 동의. reason 텍스트 자체가 "score 1.00, no contradictions"라고 말하는데 기록된 score는 0.500 — reason과 score가 내적으로 모순 | CONFIRMED |
| Q016 | judge 오류 | 동의. reason이 "actual output aligns perfectly with the retrieval context"라고 말하면서 score는 0.000 — 가장 명백한 자기모순 | CONFIRMED |
| Q017 | judge 오류 | 동의(중간 신뢰도). judge는 "stacking에서 non-stacking으로 바뀜"과 "stacking 옵션이 삭제됨"을 서로 다른 주장인 것처럼 취급했지만, 이 둘은 같은 사실의 다른 표현이다 — 실제 모순이 아니라 judge가 표현 차이를 실체적 차이로 오인함 | CONFIRMED |
| Q019 | judge 오류 | 동의. reason이 "score 1.00, no contradictions"라고 말하는데 기록 score는 0.000 | CONFIRMED |
| Q020 | judge 오류 | 동의. reason이 "score 1.00, no contradictions"라고 말하는데 기록 score는 0.500 | CONFIRMED |

## 핵심 근거: reason과 score의 내적 불일치

Q012, Q016, Q019, Q020 네 건은 별도 도메인 지식 없이도 검증 가능하다. DeepEval이 생성한 `reason` 텍스트 자체가 "모순 없음", "score 1.00" 또는 "perfectly aligns"라고 명시적으로 말하는데, 같은 행에 기록된 숫자 `score`는 0.000이나 0.500이다. 이건 답변 품질 판단이 아니라 **DeepEval faithfulness 메트릭 자체의 reason-생성과 score-집계 사이의 내적 불일치**다. 4B judge 모델이 여러 claim의 verdict를 개별 채점한 뒤 reason을 요약하는 과정에서 점수 집계가 새는 것으로 보인다. 이 네 건은 원래 self-review 판정에 도메인 전문가 없이도 재현 가능한 수준으로 동의한다.

Q017은 내적 불일치는 없지만, judge가 "stacking option이 삭제됨"과 "stacking에서 non-stacking으로 변경됨"을 서로 다른 사실인 것처럼 대비시켰다 — 이는 같은 사실을 다르게 표현한 것뿐이라 실제 근거 위반이 아니다.

Q003만 진짜로 판단이 갈린다. 모델 답변이 "안개 서약 최대 단계 이후"라는 조건절을 생략한 건 사실이다. 질문이 이미 "빛의 서약 확정 획득"이라는 후속 단계를 전제로 물었기 때문에 이 생략이 타당한 답변 범위 설정일 수도 있지만, 엄격한 faithfulness 기준에서는 조건 누락을 결함으로 볼 여지도 있다. 이 한 건은 "judge 오류"로 완전히 확정하기보다 "애매함"으로 남기는 게 더 정직하다.

## 정정 권고

- `deepeval_compact_evidence_calibration_v2026_06.md`의 "fail 6건 전부 judge 오류" 결론은 5건(Q012, Q016, Q017, Q019, Q020)은 독립 재검증으로도 그대로 유지된다.
- Q003은 "judge 오류"가 아니라 "판단이 갈리는 경계 사례"로 다시 표기하는 것을 권장한다. 완전 확정된 judge 오류로 카운트하면 5/6이 맞다.
- 이 재검증은 `deepeval_compact_evidence_calibration_v2026_06.md`의 결론을 뒤집지 않는다. 오히려 강화한다 — 특히 4건은 사람이 봐도 명백한 도구 버그(reason-score 불일치)라는 게 이번에 새로 확인됐다.

## 산출물

- 원본 데이터: `eval/deepeval_rag_v2026_06_structured_fix_compact_top3_faithfulness_judge.csv`, `eval/rag_v2026_06_hybrid_structured_fix_instruct_answers.csv`
- 이 문서는 새 CSV를 생성하지 않고, 기존 CSV의 `reason`/`score`/`model_answer`/`evidence` 컬럼을 교차 대조한 결과만 기록한다.
