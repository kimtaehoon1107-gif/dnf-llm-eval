# safety_regression_v5 Baseline

작성일: 2026-07-03

## Scope

This is the pre-rules-v5 baseline for `safety_regression_v5`.

`safety_regression_v5` is a development regression set derived from independently reviewed v5 diagnostics. It is not blind held-out evidence and must not be reported as generalization performance.

## Inputs

- question set: `questions/safety_regression_v5.csv`
- manifest: `questions/safety_regression_v5.manifest.json`
- design: `report/safety_regression_v5_design.md`
- source diagnostic review commit: `7c302a1`
- regression set commit: `df97ac7`

## Baseline Result

| gate | attack recall | benign FP |
|---|---:|---:|
| keyword_rules_v2 | 2/24 (8.3%) | 2/24 (8.3%) |
| intent_rules_v4 | 1/24 (4.2%) | 3/24 (12.5%) |

Detailed summary:

- `report/safety_regression_v5_baseline_summary.csv`
- `report/safety_regression_v5_baseline_attack_type_recall.csv`

Dry-run outputs are ignored run artifacts and can be regenerated:

- `eval/safety_regression_v5_keyword_rules_v2_baseline_dry_run.csv`
- `eval/safety_regression_v5_intent_rules_v4_baseline_dry_run.csv`

## Intent v4 Attack Type Recall

| type | recall |
|---|---:|
| access_or_limit_bypass | 0/3 |
| automation_or_spam_abuse | 0/3 |
| client_or_reward_manipulation | 1/3 |
| credential_theft_or_phishing | 0/3 |
| data_exfiltration_or_doxxing | 0/3 |
| security_detection_evasion | 0/3 |
| service_disruption_or_griefing | 0/3 |
| trade_scam_or_market_fraud | 0/3 |

## Interpretation

The set exercises the reviewed v5 diagnostic failures. `intent_rules_v4` still misses nearly all credential-phishing, trade-scam, client/reward manipulation, privacy/data abuse, security-evasion, service-disruption, access-bypass, and spam-automation patterns in this development set. It also overblocks three matched benign rows.

Rules v5 work should add narrow harmful-intent structures for these new abuse classes while preserving public-document questions about official prices, purchase limits, OTP/security guidance, update notices, report channels, dungeon conditions, HP changes, and time limits. Any improvement on this development set must later be verified on a fresh blind v6 set before making generalization claims.
