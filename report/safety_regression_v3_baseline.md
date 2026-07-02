# safety_regression_v3 Baseline

작성일: 2026-07-03

## Scope

This is the pre-rules-v3 baseline for `safety_regression_v3`.

`safety_regression_v3` is a development regression set derived from independently reviewed v3 diagnostics. It is not blind held-out evidence and must not be reported as generalization performance.

## Inputs

- question set: `questions/safety_regression_v3.csv`
- manifest: `questions/safety_regression_v3.manifest.json`
- design: `report/safety_regression_v3_design.md`
- source diagnostic review commit: `6dd1849`
- regression set commit: `af2f96f`

## Baseline Result

| gate | attack recall | benign FP |
|---|---:|---:|
| keyword_rules_v2 | 4/24 (16.7%) | 4/24 (16.7%) |
| intent_rules_v2 | 8/24 (33.3%) | 5/24 (20.8%) |

Detailed summary:

- `report/safety_regression_v3_baseline_summary.csv`
- `report/safety_regression_v3_baseline_attack_type_recall.csv`

Dry-run outputs are ignored run artifacts and can be regenerated:

- `eval/safety_regression_v3_keyword_rules_v2_baseline_dry_run.csv`
- `eval/safety_regression_v3_intent_rules_v2_baseline_dry_run.csv`

## Intent v2 Attack Type Recall

| type | recall |
|---|---:|
| answer_rule_laundering | 1/3 |
| multi_account_automation | 1/3 |
| policy_null_roleplay | 3/4 |
| priority_inversion | 1/3 |
| sanction_evasion | 0/3 |
| structural_rmt | 1/3 |
| unsupported_official_assertion | 1/5 |

## Interpretation

The set is exercising the intended v3 diagnostic failures. `intent_rules_v2` still misses most priority inversion, answer-rule laundering, sanction evasion, structural RMT, multi-account automation, and unsupported official assertion cases. It also overblocks five matched benign rows.

Rules v3 work should prioritize reducing benign false positives before broadening attack coverage. Any improvement on this development set must later be verified on a fresh blind v4 set before making generalization claims.
