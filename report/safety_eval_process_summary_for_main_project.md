# Safety Evaluation Process Summary for Main Project

작성일: 2026-07-03

## 한 줄 요약

이번 라운드는 safety gate 점수를 단순히 올리는 작업이 아니라, blind held-out 평가와 개발용 regression을 분리해 **정직하고 재현 가능한 개선 과정**을 남기는 작업이었다. 최종 fresh blind verification은 사전 선언된 `heldout_safety_v6`이며, 최종 결과는 `intent_rules_v5`가 `intent_rules_v4`보다 attack block rate를 10/24에서 12/24로 높이고 benign false positive는 0/24로 유지한 것이다.

## 최종 결론

최종 보고 대상 결과는 `heldout_safety_v6`이다.

| gate | attack block rate | benign FP rate | error count |
|---|---:|---:|---:|
| keyword_rules_v2 | 1/24 (4.2%) | 0/24 (0.0%) | 23 |
| intent_rules_v4 | 10/24 (41.7%) | 0/24 (0.0%) | 14 |
| intent_rules_v5 | 12/24 (50.0%) | 0/24 (0.0%) | 12 |

결론:

- `intent_rules_v5`는 최종 fresh blind v6에서 `intent_rules_v4`보다 개선됐다.
- 공격 차단은 10/24에서 12/24로 2문항 증가했다.
- 정상 과차단은 0/24로 유지됐다.
- v6 결과 확인 뒤 추가 튜닝은 이번 라운드에 포함하지 않는다.

최종 보고서:

- `report/safety_eval_final_report_v6.md`

## 핵심 원칙

이번 작업에서 지킨 원칙은 다음과 같다.

1. Blind held-out 작성자는 gate 규칙, 이전 결과, error analysis, regression set을 보지 않는다.
2. Held-out CSV는 freeze/hash/commit 이후 결과를 보더라도 수정하지 않는다.
3. 결과를 본 held-out은 개선용으로 직접 고치지 않고, 별도 `safety_regression_*` 개발 세트로 분리한다.
4. Error analysis는 초안 작성 후 독립 리뷰를 거친 뒤 regression 작성에 사용한다.
5. Regression 성과는 개발 성과로만 보고하며, 일반화 성능 주장은 새 fresh blind set에서만 한다.
6. v6는 결과 보기 전에 마지막 fresh blind verification으로 사전 선언했다.
7. v6 결과는 좋든 나쁘든 최종 보고서에 그대로 반영한다.

## 최종 검증 선언

v6 결과를 보기 전에 다음을 커밋으로 선언했다.

- declaration commit: `ebe38a1`
- file: `report/heldout_safety_v6_final_verification_declaration.md`
- 내용: `heldout_safety_v6`를 이번 개선 라운드의 마지막 fresh blind verification으로 삼고, 결과가 개선/동률/악화/불확실 무엇이든 최종 보고서에 그대로 포함한다.

이 선언 때문에 v6 이후 error analysis, regression_v6, rules_v6 개선은 이번 라운드에 포함하지 않았다. 그런 작업이 필요하면 새 개선 라운드로 시작해야 한다.

## 전체 흐름

```text
v1 blind held-out -> 평가 -> lineage 보존
v2 blind held-out -> 평가 -> targeted regression v2 -> rules v2
v3 blind held-out -> 평가 -> diagnostic -> independent review -> regression v3 -> rules v3
v4 blind held-out -> 평가 -> diagnostic -> independent review -> regression v4 -> rules v4
v5 blind held-out -> 평가 -> diagnostic -> independent review -> regression v5 -> rules v5
v6 blind held-out -> 사전 최종 선언 -> 평가 -> 최종 보고서 -> 라운드 종료
```

## 커밋 타임라인

| 단계 | commit | 설명 |
|---|---|---|
| v1 freeze | `fc2e561` | Freeze held-out safety set v1 |
| v1 result | `2bda334` | Evaluate held-out safety set v1 |
| v1 lineage | `69bd4e9` | Document held-out safety v1 lineage and summary |
| v2 freeze | `ea958d5` | Freeze held-out safety set v2 |
| v2 result | `6a3aa28` | Evaluate held-out safety set v2 gate dry-run |
| regression v2 | `927eed7` | Add targeted safety regression set v2 |
| rules v2 | `04fb37d` | Improve safety gates with targeted regression v2 |
| v3 freeze | `50cc912` | Freeze held-out safety set v3 |
| v3 result | `4e138b7` | Evaluate held-out safety set v3 gate dry-run |
| v3 diagnostic draft | `387e31f` | Add draft held-out safety v3 diagnostic analysis |
| v3 diagnostic review | `6dd1849` | Add independent review for held-out safety v3 diagnostic |
| regression v3 | `af2f96f` | Add safety regression set v3 |
| regression v3 baseline | `6dc20fd` | Record safety regression v3 baseline |
| rules v3 | `f50a2fa` | Improve intent safety gate with regression v3 |
| v4 freeze | `229881f` | Freeze held-out safety set v4 |
| v4 result | `5d92734` | Evaluate held-out safety set v4 |
| v4 diagnostic draft | `99ccc5d` | Add draft held-out safety v4 diagnostic analysis |
| v4 diagnostic review | `fa59048` | Add independent review for held-out safety v4 diagnostic |
| regression v4 | `1df8505` | Add safety regression set v4 |
| regression v4 baseline | `1e25c74` | Record safety regression v4 baseline |
| rules v4 | `f7f4fda` | Improve intent safety gate with regression v4 |
| v5 freeze | `c364d80` | Freeze held-out safety set v5 |
| v5 result | `5469a6a` | Evaluate held-out safety set v5 |
| v5 diagnostic draft | `b68ec4e` | Add draft held-out safety v5 diagnostic analysis |
| v5 diagnostic review | `7c302a1` | Add independent review for held-out safety v5 diagnostic |
| regression v5 | `df97ac7` | Add safety regression set v5 |
| regression v5 baseline | `eed4e68` | Record safety regression v5 baseline |
| rules v5 | `b802865` | Improve intent safety gate with regression v5 |
| v6 freeze | `fd99061` | Freeze held-out safety set v6 |
| v6 final declaration | `ebe38a1` | Declare held-out safety v6 as final verification |
| v6 result | `8f1393c` | Evaluate held-out safety set v6 |
| final report | `7b71347` | Finalize safety evaluation round with v6 result |

## Held-out 결과 요약

| set | 비교 대상 | attack block rate | benign FP rate | 해석 |
|---|---|---:|---:|---|
| v1 | keyword | 4/24 (16.7%) | 0/24 (0.0%) | 초기 keyword 기준 |
| v1 | intent | 6/24 (25.0%) | 0/24 (0.0%) | keyword보다 높지만 절대 수치 낮음 |
| v2 | keyword | 8/24 (33.3%) | 0/24 (0.0%) | v2에서는 keyword가 intent보다 높음 |
| v2 | intent | 7/24 (29.2%) | 0/24 (0.0%) | intent 우위 주장 불가 |
| v3 | intent_rules_v2 | 13/24 (54.2%) | 3/24 (12.5%) | recall 상승, overrefusal 증가 |
| v4 | intent_rules_v2 | 15/24 (62.5%) | 0/24 (0.0%) | fresh blind 개선 확인 |
| v4 | intent_rules_v3 | 16/24 (66.7%) | 0/24 (0.0%) | v3 대비 +1, FP 유지 |
| v5 | intent_rules_v3 | 8/24 (33.3%) | 0/24 (0.0%) | v5에서는 낮은 recall |
| v5 | intent_rules_v4 | 8/24 (33.3%) | 0/24 (0.0%) | rules_v4는 v5에서 동률 |
| v6 | intent_rules_v4 | 10/24 (41.7%) | 0/24 (0.0%) | 최종 비교 기준 |
| v6 | intent_rules_v5 | 12/24 (50.0%) | 0/24 (0.0%) | 최종 fresh blind 개선 |

주의:

- v1~v5는 과정과 개발 판단의 근거다.
- 최종 일반화 주장은 사전 선언된 v6 결과만 기준으로 한다.

## Regression 개발 결과

Regression set은 held-out 결과를 본 뒤 만든 개발용 세트다. 따라서 일반화 성능 근거로 쓰지 않는다.

| regression set | baseline | after rules | 의미 |
|---|---:|---:|---|
| safety_regression_v2 | intent 6/24, FP 0/24 | intent_rules_v2 24/24, FP 0/24 | 초기 실패 유형 보강 |
| safety_regression_v3 | intent_rules_v2 8/24, FP 5/24 | intent_rules_v3 24/24, FP 0/24 | v3 overrefusal/FN 보강 |
| safety_regression_v4 | intent_rules_v3 9/24, FP 6/24 | intent_rules_v4 24/24, FP 0/24 | v4 diagnostic 기반 보강 |
| safety_regression_v5 | intent_rules_v4 1/24, FP 3/24 | intent_rules_v5 24/24, FP 0/24 | v5 diagnostic 기반 새 abuse 범주 보강 |

rules_v5 추가 검증:

| check | result |
|---|---:|
| safety_regression_v5 | 24/24, FP 0/24 |
| safety_regression_v4 | 24/24, FP 0/24 |
| safety_regression_v3 | 24/24, FP 0/24 |
| safety_regression_v2 | 24/24, FP 0/24 |
| safety_overrefusal_questions | FP 0/20 |
| safety_intent_benign_expansion | FP 0/30 |
| safety_intent_attack_expansion | 30/30 |
| default safety classifier bundle | 50/50, FP 0/50 |

## 주요 파일

최종/핵심 파일:

- `report/safety_eval_final_report_v6.md`
- `report/heldout_safety_v6_final_verification_declaration.md`
- `report/heldout_safety_v6_results.md`
- `report/heldout_safety_v6_gate_summary.csv`
- `report/heldout_safety_v6_attack_type_recall.csv`
- `questions/heldout_safety_v6.csv`
- `questions/heldout_safety_v6.manifest.json`
- `report/heldout_safety_v6_preregistration.md`
- `scripts/safety_intent.py`

개발 맥락 파일 (7/4 정리: v1~v5 raw 산출물은 `report/archive/safety_v1_v5_process/`로 이동. 내용은 그대로, 경로만 archive로 바뀜):

- `report/archive/safety_v1_v5_process/safety_rules_v5_update.md`
- `report/archive/safety_v1_v5_process/safety_rules_v5_update_summary.csv`
- `report/archive/safety_v1_v5_process/safety_regression_v5_baseline.md`
- `report/archive/safety_v1_v5_process/safety_regression_v5_baseline_summary.csv`
- `questions/safety_regression_v5.csv`
- `questions/safety_regression_v5.manifest.json`
- `report/archive/safety_v1_v5_process/safety_regression_v5_design.md`
- `report/archive/safety_v1_v5_process/heldout_safety_v5_error_analysis_reviewed.md`
- `report/archive/safety_v1_v5_process/heldout_safety_v5_independent_review_notes.md`

v1~v5 전체 raw 산출물(preregistration/results/diagnostic/independent review/regression/rules update, 총 73개 파일)은 전부 `report/archive/safety_v1_v5_process/`에 있다. 이 문서의 "전체 흐름"·"커밋 타임라인"·"Held-out 결과 요약" 표만으로 v1~v5 과정을 파악하기에 충분하므로, raw 파일은 필요할 때만 열어보면 된다.

## v6 상세

v6 freeze:

- freeze commit: `fd99061b9c6b309a9034d9f0cf57ea5d44a223f4`
- CSV sha256: `bce8f120af1776736428b092ebd96f126eb39b75563f2cecec4e2a57fe9980b1`
- rows: 48
- attack / benign: 24 / 24
- forbidden file contents viewed: false
- evaluation before freeze: false

v6 결과:

| attack type | intent_rules_v4 | intent_rules_v5 |
|---|---:|---:|
| credential_phishing_privacy_harassment | 0/4 | 1/4 |
| game_exploit_and_reward_abuse | 4/4 | 4/4 |
| automation_botting_and_client_tampering | 3/4 | 3/4 |
| malware_prompt_injection_and_cyber_abuse | 1/4 | 1/4 |
| fraud_marketplace_and_economy_abuse | 2/4 | 3/4 |
| real_world_harm_self_harm_threats | 0/4 | 0/4 |

개선된 부분:

- credential/phishing/privacy-harassment에서 1개 추가 차단
- fraud/marketplace/economy-abuse에서 1개 추가 차단

남은 한계:

- 최종 blind 기준 attack block rate는 50.0%로, 아직 충분히 높다고 보기는 어렵다.
- 특히 real-world harm/self-harm/threats는 0/4로 남았다.
- malware/prompt-injection/cyber-abuse도 1/4에 그쳤다.
- 이 한계는 최종 보고서에 그대로 남겨야 한다.

## 본프로젝트에 붙일 때 권장 표현

권장 문장:

```text
이번 safety gate 개선 라운드는 v6를 사전 선언된 최종 fresh blind verification으로 삼아 종료했다. 개발용 regression에서는 intent_rules_v5가 목표 세트를 모두 통과했지만, 일반화 주장은 regression이 아니라 v6 결과만 기준으로 한다. 최종 v6에서 intent_rules_v5는 intent_rules_v4 대비 attack block rate를 10/24에서 12/24로 높였고, benign false positive는 0/24로 유지했다. 따라서 이번 라운드의 결론은 '제한적이지만 재현 가능한 개선'이다.
```

피해야 할 표현:

```text
regression_v5에서 100%였으므로 safety 문제가 해결됐다.
```

```text
v6 이후 다시 튜닝하면 최종 결과도 더 좋아진다.
```

```text
v1~v6 모든 결과를 단순 평균해 최종 성능으로 보자.
```

## 현재 상태

현재 라운드는 종료됐다.

마지막 커밋:

- `7b71347 Finalize safety evaluation round with v6 result`

남아 있는 unrelated untracked 파일:

- `report/research_overview_master.md`
- `report/research_summary_and_roadmap.md`

이 두 파일은 이번 safety evaluation 라운드 산출물로 커밋하지 않았다.

## 다음 라운드를 시작한다면

다음 개선을 하려면 이번 라운드를 이어서 고치지 말고 새 라운드로 시작한다.

권장 순서:

```text
1. v6 결과 기반 diagnostic 작성
2. 독립 리뷰
3. safety_regression_v6 작성
4. rules_v6 개발
5. 새 fresh blind v7 작성/평가
6. v7 결과를 새 라운드 최종 결과로 보고
```

단, 이 경우 v6는 더 이상 이번 라운드의 개선 입력이 아니라 다음 라운드의 출발점으로 취급한다.
