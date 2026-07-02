# Held-out Safety v3 Results

작성일: 2026-07-03

## Status

`heldout_safety_v3` was authored in a separate blind thread and frozen before evaluation.

- freeze commit: `50cc912 Freeze held-out safety set v3`
- CSV sha256: `bd4ea16f92fff798f1763a7cd990da4c2c8ef36021321c63d2ce33671011cdea`
- row count: 48
- attack / benign: 24 / 24
- manifest sha256 matched CSV before freeze: yes

This result is a post-improvement blind check. The v3 CSV, manifest, preregistration, safety rules, prompts, and thresholds must not be modified after viewing these results.

## Evaluation

Gate dry-run evaluation was run for four combinations:

| gate | source commit | attack recall | benign FP |
|---|---|---:|---:|
| keyword_rules_v1 | `927eed7` | 6/24 (25.0%) | 2/24 (8.3%) |
| intent_rules_v1 | `927eed7` | 6/24 (25.0%) | 1/24 (4.2%) |
| keyword_rules_v2 | `50cc912` | 7/24 (29.2%) | 2/24 (8.3%) |
| intent_rules_v2 | `50cc912` | 13/24 (54.2%) | 3/24 (12.5%) |

Detailed summaries:

- `report/heldout_safety_v3_gate_summary.csv`
- `report/heldout_safety_v3_attack_type_recall.csv`

Dry-run output CSVs are ignored run artifacts and can be regenerated:

- `eval/heldout_safety_v3_keyword_rules_v1_dry_run.csv`
- `eval/heldout_safety_v3_intent_rules_v1_dry_run.csv`
- `eval/heldout_safety_v3_keyword_rules_v2_dry_run.csv`
- `eval/heldout_safety_v3_intent_rules_v2_dry_run.csv`

## Attack Type Recall

| type | keyword v1 | intent v1 | keyword v2 | intent v2 |
|---|---:|---:|---:|---:|
| automation_abuse | 2/3 | 0/3 | 2/3 | 2/3 |
| exploit_request | 0/3 | 0/3 | 1/3 | 2/3 |
| fake_evidence | 1/3 | 0/3 | 1/3 | 2/3 |
| jailbreak | 1/3 | 1/3 | 1/3 | 1/3 |
| prompt_injection | 1/3 | 2/3 | 1/3 | 1/3 |
| prompt_leakage | 0/3 | 2/3 | 0/3 | 3/3 |
| real_money_trade | 1/3 | 1/3 | 1/3 | 1/3 |
| unsupported_speculation | 0/3 | 0/3 | 0/3 | 1/3 |

## Interpretation

`intent_rules_v2` substantially improved attack recall on the fresh blind v3 set, from 6/24 to 13/24. This is evidence that the targeted regression work generalized beyond the development set.

The improvement is not cost-free: benign false positives also increased from 1/24 to 3/24 for the intent gate. Therefore this is not a clean Pareto improvement. The result supports "better attack coverage with higher overrefusal risk," not "strictly better in all dimensions."

`keyword_rules_v2` changed little on v3: attack recall rose from 6/24 to 7/24 with the same benign FP count. The keyword gate remains a simple baseline rather than the primary safety-intent detector.

The strongest intent v2 gains were on prompt leakage, exploit requests, fake evidence, automation abuse, and unsupported speculation. Remaining misses include prompt injection, jailbreak, real-money trade, and several paraphrased abuse requests.

## Next Step

Do not tune directly on v3 and then claim v3 improvement. If v3 failures are used for development, promote them into a new targeted regression set and run a fresh blind v4 afterward.
