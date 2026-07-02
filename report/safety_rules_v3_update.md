# Safety Rules v3 Update

작성일: 2026-07-03

## Scope

This update changes only the intent classifier rules:

- `intent_rules_v2` -> `intent_rules_v3`
- file changed: `scripts/safety_intent.py`

The keyword gate remains `keyword_rules_v2`.

This is development work based on independently reviewed `heldout_safety_v3` diagnostics and `safety_regression_v3`. It is not a new blind held-out result. Do not report improvement on v3 as official generalization performance. The next generalization check must be a fresh blind v4 set.

## Inputs

- reviewed diagnostic commit: `6dd1849`
- regression v3 commit: `af2f96f`
- baseline commit: `6dc20fd`
- regression set: `questions/safety_regression_v3.csv`
- baseline report: `report/safety_regression_v3_baseline.md`

## Rule Changes

`intent_rules_v3` adds two kinds of changes.

First, it adds a narrow public-source negated-trigger guard. This allows benign questions that explicitly say they are not asking for private conditions, hidden instructions, macro design, bot flows, or sanction-evasion tips, while asking for public patch-note or documented UI/policy content. The guard still blocks if harmful execution, evasion, automation, RMT, fabricated official evidence, or rule-override markers are present.

Second, it adds structural attack patterns for:

- priority inversion
- answer-rule laundering
- policy-null roleplay
- fabricated or unsupported official assertions
- sanction evasion
- multi-account automation abuse
- structural real-money trade

## Regression v3 Result

| phase | gate | attack recall | benign FP |
|---|---|---:|---:|
| baseline | intent_rules_v2 | 8/24 (33.3%) | 5/24 (20.8%) |
| after rules | intent_rules_v3 | 24/24 (100.0%) | 0/24 (0.0%) |

Attack-type comparison:

- `report/safety_regression_v3_rules_v3_attack_type_recall.csv`

Summary:

- `report/safety_rules_v3_update_summary.csv`

Dry-run artifact:

- `eval/safety_regression_v3_intent_rules_v3_dry_run.csv`

## Additional Checks

| set | gate | attack recall | benign FP |
|---|---|---:|---:|
| safety_regression_v2 | intent_rules_v3 | 24/24 (100.0%) | 0/24 (0.0%) |
| safety_overrefusal_questions | intent_rules_v3 | n/a | 0/20 (0.0%) |
| safety_intent_benign_expansion | intent_rules_v3 | n/a | 0/30 (0.0%) |
| safety_intent_attack_expansion | intent_rules_v3 | 30/30 (100.0%) | n/a |
| default safety classifier bundle | intent_rules_v3 | 50/50 (100.0%) | 0/50 (0.0%) |

Classifier outputs:

- `eval/safety_intent_classifier_rules_v3_summary.csv`
- `eval/safety_intent_classifier_rules_v3_detail.csv`

## Interpretation

The targeted development objective was met on `safety_regression_v3`: the new rules cover the reviewed v3 failure structures while removing the matched benign false positives in that development set.

This should be treated as a rules-development result, not as blind validation. Because `safety_regression_v3` was derived from reviewed v3 failures, the next trustworthy test is a fresh blind v4 evaluation performed after this commit is frozen.
