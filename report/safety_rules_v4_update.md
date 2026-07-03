# Safety Rules v4 Update

Created: 2026-07-03

## Scope

This update changes only the intent classifier rules:

- `intent_rules_v3` -> `intent_rules_v4`
- file changed: `scripts/safety_intent.py`

The keyword gate remains `keyword_rules_v2`.

This is development work based on independently reviewed `heldout_safety_v4` diagnostics and `safety_regression_v4`. It is not a new blind held-out result. Do not report improvement on `safety_regression_v4` as generalization performance. The next trustworthy generalization check must be a fresh blind v5 set.

## Inputs

- reviewed diagnostic commit: `fa59048`
- regression v4 set commit: `1df8505`
- regression v4 baseline commit: `1e25c74`
- regression set: `questions/safety_regression_v4.csv`
- baseline report: `report/safety_regression_v4_baseline.md`

## Rule Changes

`intent_rules_v4` adds narrow structural coverage for the reviewed v4 failure patterns:

- private refusal template and hidden blocking-criteria leakage
- no-refusal or verification-mode laundering with harmful payloads
- development/test framing used to launder automation, RMT, or bypass requests
- resource, material, cost, entry-limit, and restore/reclaim bypass procedures
- account lookup automation across DNF ON or account/character lookup surfaces
- external cash-sale routing, reward monetization, account valuation, and sale-listing copy

It also extends the public-source negated-trigger guard so benign questions that explicitly ask for documented patch-note facts, documented UI behavior, item trade type, price, purchase limits, and public lookup scope are not blocked merely because they mention nearby risky words.

## Regression v4 Result

| phase | gate | attack recall | benign FP |
|---|---|---:|---:|
| baseline | intent_rules_v3 | 9/24 (37.5%) | 6/24 (25.0%) |
| after rules | intent_rules_v4 | 24/24 (100.0%) | 0/24 (0.0%) |

Attack-type comparison:

- `report/safety_regression_v4_rules_v4_attack_type_recall.csv`

Summary:

- `report/safety_rules_v4_update_summary.csv`

Dry-run artifact:

- `eval/safety_regression_v4_intent_rules_v4_dry_run.csv`

## Additional Checks

| set | gate | attack recall | benign FP |
|---|---|---:|---:|
| safety_regression_v3 | intent_rules_v4 | 24/24 (100.0%) | 0/24 (0.0%) |
| safety_regression_v2 | intent_rules_v4 | 24/24 (100.0%) | 0/24 (0.0%) |
| safety_overrefusal_questions | intent_rules_v4 | n/a | 0/20 (0.0%) |
| safety_intent_benign_expansion | intent_rules_v4 | n/a | 0/30 (0.0%) |
| safety_intent_attack_expansion | intent_rules_v4 | 30/30 (100.0%) | n/a |
| default safety classifier bundle | intent_rules_v4 | 50/50 (100.0%) | 0/50 (0.0%) |

Classifier outputs:

- `eval/safety_intent_classifier_rules_v4_summary.csv`
- `eval/safety_intent_classifier_rules_v4_detail.csv`

## Interpretation

The targeted development objective was met on `safety_regression_v4`: the new intent rules cover the reviewed v4 failure structures while removing the matched benign false positives in that development set.

This should be treated as a rules-development result, not blind validation. Because `safety_regression_v4` was derived from reviewed v4 failures, the next trustworthy test is a fresh blind v5 evaluation performed after this rules commit is frozen.
