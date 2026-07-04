# Safety Rules v5 Update

Created: 2026-07-03

## Scope

This update changes only the intent classifier rules:

- `intent_rules_v4` -> `intent_rules_v5`
- file changed: `scripts/safety_intent.py`

The keyword gate remains `keyword_rules_v2`.

This is development work based on independently reviewed `heldout_safety_v5` diagnostics and `safety_regression_v5`. It is not a new blind held-out result. Do not report improvement on `safety_regression_v5` as generalization performance. The next trustworthy generalization check must be a fresh blind v6 set.

## Inputs

- reviewed diagnostic commit: `7c302a1`
- regression v5 set commit: `df97ac7`
- regression v5 baseline commit: `eed4e68`
- regression set: `questions/safety_regression_v5.csv`
- baseline report: `report/safety_regression_v5_baseline.md`

## Rule Changes

`intent_rules_v5` adds narrow structural coverage for the reviewed v5 failure patterns:

- credential theft and phishing copy, including login information, OTP/authentication-code harvesting, impersonation, and malicious-link lures
- trade scam and market fraud, including deceptive item-trade copy, price deception, and market-notice misuse
- client or reward manipulation, including reward probability/display tampering, exploration time/progress manipulation, HP manipulation, and client-state tampering
- data exfiltration and doxxing, including unauthorized update-data extraction, secret account/inventory collection, and personal-information publication
- security detection evasion, including hiding client/account manipulation from security controls
- service disruption and griefing, including forced party failure and traffic-based disruption
- entry, weekly-limit, and purchase-limit spoofing
- report-channel spam automation and bulk false-report submission

It also extends the public-source negated-trigger guard so benign questions that explicitly ask for official public notices, prices, purchase limits, first-server opening notices, entry conditions, HP changes, time limits, and report-channel guidance are not blocked merely because they mention nearby risky words.

## Regression v5 Result

| phase | gate | attack recall | benign FP |
|---|---|---:|---:|
| baseline | intent_rules_v4 | 1/24 (4.2%) | 3/24 (12.5%) |
| after rules | intent_rules_v5 | 24/24 (100.0%) | 0/24 (0.0%) |

Attack-type comparison:

- `report/safety_regression_v5_rules_v5_attack_type_recall.csv`

Summary:

- `report/safety_rules_v5_update_summary.csv`

Dry-run artifact:

- `eval/safety_regression_v5_intent_rules_v5_dry_run.csv`

## Additional Checks

| set | gate | attack recall | benign FP |
|---|---|---:|---:|
| safety_regression_v4 | intent_rules_v5 | 24/24 (100.0%) | 0/24 (0.0%) |
| safety_regression_v3 | intent_rules_v5 | 24/24 (100.0%) | 0/24 (0.0%) |
| safety_regression_v2 | intent_rules_v5 | 24/24 (100.0%) | 0/24 (0.0%) |
| safety_overrefusal_questions | intent_rules_v5 | n/a | 0/20 (0.0%) |
| safety_intent_benign_expansion | intent_rules_v5 | n/a | 0/30 (0.0%) |
| safety_intent_attack_expansion | intent_rules_v5 | 30/30 (100.0%) | n/a |
| default safety classifier bundle | intent_rules_v5 | 50/50 (100.0%) | 0/50 (0.0%) |

Classifier outputs:

- `eval/safety_intent_classifier_rules_v5_summary.csv`
- `eval/safety_intent_classifier_rules_v5_detail.csv`

## Interpretation

The targeted development objective was met on `safety_regression_v5`: the new intent rules cover the reviewed v5 failure structures while removing the matched benign false positives in that development set.

This should be treated as a rules-development result, not blind validation. Because `safety_regression_v5` was derived from reviewed v5 failures, the next trustworthy test is a fresh blind v6 evaluation performed after this rules commit is frozen.
