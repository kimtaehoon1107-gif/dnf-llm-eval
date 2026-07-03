# safety_regression_v4 Baseline

작성일: 2026-07-03

## Scope

This is the pre-rules-v4 baseline for `safety_regression_v4`.

`safety_regression_v4` is a development regression set derived from independently reviewed v4 diagnostics. It is not blind held-out evidence and must not be reported as generalization performance.

## Inputs

- question set: `questions/safety_regression_v4.csv`
- manifest: `questions/safety_regression_v4.manifest.json`
- design: `report/safety_regression_v4_design.md`
- source diagnostic review commit: `fa59048`
- regression set commit: `1df8505`

## Baseline Result

| gate | attack recall | benign FP |
|---|---:|---:|
| keyword_rules_v2 | 3/24 (12.5%) | 4/24 (16.7%) |
| intent_rules_v3 | 9/24 (37.5%) | 6/24 (25.0%) |

Detailed summary:

- `report/safety_regression_v4_baseline_summary.csv`
- `report/safety_regression_v4_baseline_attack_type_recall.csv`

Dry-run outputs are ignored run artifacts and can be regenerated:

- `eval/safety_regression_v4_keyword_rules_v2_baseline_dry_run.csv`
- `eval/safety_regression_v4_intent_rules_v3_baseline_dry_run.csv`

## Intent v3 Attack Type Recall

| type | recall |
|---|---:|
| account_lookup_automation | 2/3 |
| account_valuation_sale_listing | 0/3 |
| dev_test_payload_laundering | 2/3 |
| entry_limit_reclaim_repro | 2/3 |
| no_refusal_mode_payload | 0/3 |
| private_refusal_template_leakage | 1/3 |
| resource_bypass_procedure | 0/3 |
| reward_cash_trade_route | 2/3 |

## Interpretation

The set exercises the reviewed v4 diagnostic failures. `intent_rules_v3` still misses most no-refusal mode payload, private refusal template leakage, resource-bypass procedure, account-valuation sale/listing, and several RMT/automation/generalized exploit cases. It also overblocks six matched benign rows.

Rules v4 work should first preserve benign public-document questions and negated-abuse questions, then add narrow structural attack patterns. Any improvement on this development set must later be verified on a fresh blind v5 set before making generalization claims.
