# safety_regression_v2 Rule Update

작성일: 2026-07-02

## Scope

이 작업은 blind held-out 평가가 아니라, `safety_regression_v2`를 이용한 개발/회귀 개선이다. `heldout_safety_v1`과 `heldout_safety_v2`는 이미 결과를 본 frozen set이므로, 이번 개선 결과를 blind 일반화 성능으로 주장하지 않는다. 최종 일반화 확인은 새 blind set에서 다시 해야 한다.

## Changed Rules

- `scripts/run_rag_local_llm_eval.py`
  - keyword gate version을 `keyword_rules_v2`로 올렸다.
  - prompt leakage, fake evidence, exploit request, automation abuse, real-money trade, unsupported speculation 조합 규칙을 보강했다.
  - 방어용 테스트, 안전한 거절 예시, 공개 문서 근거 문의, 제재 정책 문의 같은 benign safety-meta 질문을 먼저 허용하는 guard를 추가했다.
- `scripts/safety_intent.py`
  - intent gate version을 `intent_rules_v2`로 올렸다.
  - hidden prompt/context/rubric disclosure, fabricated official evidence, bug-abuse procedure, bot design, cash-trade promotion, unsupported future threshold claims를 더 잘 잡도록 규칙을 보강했다.
  - matched benign near-miss를 허용하는 defensive safety-meta guard를 추가했다.

## Regression Result

| set | phase | gate | attack recall | benign FP |
|---|---|---|---:|---:|
| safety_regression_v2 | baseline | keyword | 6/24 (25.0%) | 2/24 (8.3%) |
| safety_regression_v2 | baseline | intent | 6/24 (25.0%) | 0/24 (0.0%) |
| safety_regression_v2 | after rules | keyword | 24/24 (100.0%) | 0/24 (0.0%) |
| safety_regression_v2 | after rules | intent | 24/24 (100.0%) | 0/24 (0.0%) |

Attack-type comparison is recorded in `report/safety_regression_v2_attack_type_compare.csv`.

## Overrefusal Checks

| set | gate | benign blocked | benign total | FP rate |
|---|---|---:|---:|---:|
| safety_overrefusal_questions | keyword | 0 | 20 | 0.0% |
| safety_overrefusal_questions | intent | 0 | 20 | 0.0% |
| safety_intent_benign_expansion | keyword | 0 | 30 | 0.0% |
| safety_intent_benign_expansion | intent | 0 | 30 | 0.0% |

## Existing Attack Expansion Check

| set | gate | attack blocked | attack total | recall |
|---|---|---:|---:|---:|
| safety_intent_attack_expansion | keyword | 5 | 30 | 16.7% |
| safety_intent_attack_expansion | intent | 30 | 30 | 100.0% |

The keyword gate remains an honest keyword baseline. The intent gate is the improved rule classifier for broader safety intent detection.

## Default Classifier Bundle

`scripts/evaluate_safety_intent_classifier.py` was run with post-rule outputs:

- `eval/safety_intent_classifier_post_rules_summary.csv`
- `eval/safety_intent_classifier_post_rules_detail.csv`

Summary:

| classifier | attack recall | false positive rate | accuracy |
|---|---:|---:|---:|
| keyword_gate | 0.300 | 0.000 | 0.650 |
| intent_classifier | 1.000 | 0.000 | 1.000 |

## Interpretation

The targeted regression goal was met: previously missed prompt leakage, fake evidence, exploit request, unsupported speculation, automation, and RMT patterns are now blocked on the development regression set without increasing measured benign false positives on the checked benign sets.

This is not a new blind held-out claim. The next trustworthy generalization check should be a fresh blind set, separate from v1, v2, and `safety_regression_v2`.
