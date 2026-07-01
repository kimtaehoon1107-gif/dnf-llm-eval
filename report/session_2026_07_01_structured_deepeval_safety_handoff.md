# 2026-07-01 structured, DeepEval, safety handoff

작성일: 2026-07-01
브랜치: `codex/v2026-06-results`

## 오늘 진행한 흐름

사용자 요청은 "쭉 리뷰하면서 각 단계별로 끝날 때마다 수정하고 정리하면서 끝까지 진행"이었다. 이에 따라 단계별로 리뷰, 수정, 검증, 문서화, 커밋을 반복했다.

## 1. Structured answer completeness fix

커밋:

- `4dc04e7 Improve v2026_06 structured answer completeness`
- 이전 관련 커밋: `af73051 Improve structured v2026_06 answer grounding`

핵심 변경:

- `scripts/run_rag_local_llm_eval.py`에서 structured change record 매칭 신호를 확장했다.
- patch change context에 `must_include`, `answer_hint`, `answer_requirement`를 추가했다.
- `data/snapshots/2026-06-official-updates/structured/change_records.json`에 Q003, Q010, Q014 관련 record를 보강했다.
- `questions/regression_questions_v2026_06_answer_completeness.csv`를 추가했다.

결과:

| run | factual proxy | format proxy | meta reasoning | avg latency |
|---|---:|---:|---:|---:|
| before | 16 / 20 | 20 / 20 | 0 | 4.273s |
| after | 20 / 20 | 20 / 20 | 0 | 4.399s |

Regression:

- Q001/Q012 structured fix regression: 2/2
- Q003/Q010/Q013/Q014/Q018 answer completeness regression: 5/5

문서:

- `report/structured_fix_iteration_v2026_06.md`
- `report/benchmark_questions_v2026_06_design.md`
- `report/v2026_06_closing_review.md`

## 2. DeepEval compact evidence calibration

커밋:

- `1d8252e Calibrate DeepEval compact evidence cases`

핵심 변경:

- `scripts/export_deepeval_rag_cases.py`에 `--context-mode full|compact`와 `--compact-top-k`를 추가했다.
- Compact mode는 `structured_context`, 사람이 만든 `evidence`, top retrieved chunk를 합쳐 judge context를 줄인다.
- `.venv/deepeval` 격리 환경에서 DeepEval faithfulness judge를 실행했다.

결과:

| setting | context blocks avg | faithfulness pass | avg score | errors |
|---|---:|---:|---:|---:|
| compact top-1 | 2.45 | 12 / 20 | 0.690 | 0 |
| compact top-3 | 4.45 | 14 / 20 | 0.735 | 0 |

수동 리뷰:

- Top-3 compact fail 6건(Q003, Q012, Q016, Q017, Q019, Q020)은 모두 생성 수정 대상이 아니라 judge false positive 또는 self-consistency 오류로 분류했다.
- `qwen3:8b` judge도 시도했지만 15분 제한 안에 완료되지 않아 중단했다.

문서:

- `report/deepeval_compact_evidence_calibration_v2026_06.md`
- `eval/deepeval_rag_v2026_06_structured_fix_compact_top3_manual_review.csv`

결론:

- DeepEval faithfulness는 자동 최종 판정자가 아니라 manual review queue 정렬용으로 쓴다.
- 다음 judge 개선은 custom GEval 또는 JSON rubric judge가 더 적합하다.

## 3. Intent safety gate end-to-end

커밋:

- `a21bd4f Run intent safety gate end-to-end`

실행 범위:

| dataset | questions | expected blocked | blocked | success | failed |
|---|---:|---:|---:|---:|---:|
| explicit adversarial | 10 | 10 | 10 | 0 | 0 |
| stealth adversarial | 10 | 10 | 10 | 0 | 0 |
| attack expansion | 30 | 30 | 30 | 0 | 0 |
| overrefusal | 20 | 0 | 0 | 20 | 0 |
| benign expansion | 30 | 0 | 0 | 30 | 0 |
| total | 100 | 50 | 50 | 50 | 0 |

결론:

- Intent safety gate는 실제 RAG 생성 경로에서 공격 recall 50/50, 정상 false positive 0/50을 기록했다.
- 기존 keyword gate의 stealth 0/10 한계는 intent gate에서 현재 보유 stealth set 기준 10/10 차단으로 개선됐다.
- 다음 과제는 새 held-out paraphrase/stealth set과 output safety checker다.

문서:

- `report/safety_intent_e2e_gate_test.md`
- `eval/safety_intent_e2e_summary.csv`
- `eval/safety_intent_e2e_intent_distribution.csv`

## 4. 최종 문서 업데이트

업데이트한 핵심 문서:

- `report/final_closing_review.md`
- `report/final_portfolio_report.md`
- `report/application_summary.md`
- `report/README.md`

반영한 최신 결론:

- 2026-06 structured fix: factual proxy 20/20, format proxy 20/20
- DeepEval compact top-3: 자동 pass 14/20, 남은 6건은 수동 리뷰에서 judge 이슈
- Intent safety gate e2e: 공격 50/50 차단, 정상 50/50 통과

## 검증

마지막으로 실행한 검증:

- `python scripts\smoke_check.py`
- `python -m py_compile scripts\export_deepeval_rag_cases.py scripts\run_deepeval_rag_judge.py`
- `git diff --check`
- 주요 CSV 행 수 확인

## 다음 추천 순서

1. Custom judge rubric 구현
   - DeepEval 기본 faithfulness 대신 JSON 출력 강제 judge를 만든다.
   - 필드 후보: `factual_match`, `completeness`, `unsupported_addition`, `live_server_misread`, `verdict`, `reason`.

2. 새 held-out safety set 추가
   - 오늘 intent gate는 현재 보유 세트에서는 통과했다.
   - 다음은 모델이나 사람이 새로 만든 paraphrase/stealth 공격과 더 큰 정상 문의 세트로 과적합을 점검한다.

3. Structured record 충돌 처리
   - record가 늘었을 때 한 질문에 여러 record가 붙는 경우 `needs_review`로 빼는 정책이 필요하다.
   - `applies_to_skill`, `applies_to_option`, `applies_to_question_type` 같은 스코프 필드를 추가하는 방향이 좋다.

4. Final report 수치 동결
   - 현재 핵심 문서는 최신 수치를 반영했다.
   - 제출 직전에는 `report/README.md`의 읽기 순서대로 한 번 더 검수하면 된다.
