# Held-out Safety v6 Results

## Freeze and Integrity

- Freeze commit: `fd99061b9c6b309a9034d9f0cf57ea5d44a223f4`
- CSV: `questions/heldout_safety_v6.csv`
- CSV sha256: `bce8f120af1776736428b092ebd96f126eb39b75563f2cecec4e2a57fe9980b1`
- Manifest: `questions/heldout_safety_v6.manifest.json`
- Preregistration: `report/heldout_safety_v6_preregistration.md`
- Row count / attack_count / benign_count: 48 / 24 / 24
- CSV sha256 matched the manifest sha256 before evaluation.
- CSV/manifest/preregistration modified: no
- Gate implementation modified: no
- Official v6 CSV modified after results: no
- Commit created: no
- Dry-run errors: no (`dry_run_error_count=0` for all three gates)

Evaluation used a deterministic safety-gate dry run with no model calls. `keyword_rules_v2` and `intent_rules_v5` were evaluated from the freeze commit; `intent_rules_v4` was loaded from the prior rules commit `c364d80` without modifying the working tree. Dry-run detail files were not persisted; only the requested report summaries were written.

## Gate Metrics

Error count is `false_negative_count + false_positive_count`, where unblocked attack rows are false negatives and blocked benign rows are false positives.

| Gate | Mode | Rules commit | Attack block rate | Benign FP rate | Error count | Dry-run errors |
|---|---|---:|---:|---:|---:|---:|
| `keyword_rules_v2` | `keyword` | `fd99061` | 1/24 (4.2%) | 0/24 (0.0%) | 23 | 0 |
| `intent_rules_v4` | `intent` | `c364d80` | 10/24 (41.7%) | 0/24 (0.0%) | 14 | 0 |
| `intent_rules_v5` | `intent` | `fd99061` | 12/24 (50.0%) | 0/24 (0.0%) | 12 | 0 |

## Attack Type Recall

Attack type labels follow the frozen manifest balance groups. The v6 CSV was not edited to add labels.

| Gate | Attack type | Recall |
|---|---|---:|
| `keyword_rules_v2` | `credential_phishing_privacy_harassment` | 0/4 (0.0%) |
| `keyword_rules_v2` | `game_exploit_and_reward_abuse` | 0/4 (0.0%) |
| `keyword_rules_v2` | `automation_botting_and_client_tampering` | 1/4 (25.0%) |
| `keyword_rules_v2` | `malware_prompt_injection_and_cyber_abuse` | 0/4 (0.0%) |
| `keyword_rules_v2` | `fraud_marketplace_and_economy_abuse` | 0/4 (0.0%) |
| `keyword_rules_v2` | `real_world_harm_self_harm_threats` | 0/4 (0.0%) |
| `intent_rules_v4` | `credential_phishing_privacy_harassment` | 0/4 (0.0%) |
| `intent_rules_v4` | `game_exploit_and_reward_abuse` | 4/4 (100.0%) |
| `intent_rules_v4` | `automation_botting_and_client_tampering` | 3/4 (75.0%) |
| `intent_rules_v4` | `malware_prompt_injection_and_cyber_abuse` | 1/4 (25.0%) |
| `intent_rules_v4` | `fraud_marketplace_and_economy_abuse` | 2/4 (50.0%) |
| `intent_rules_v4` | `real_world_harm_self_harm_threats` | 0/4 (0.0%) |
| `intent_rules_v5` | `credential_phishing_privacy_harassment` | 1/4 (25.0%) |
| `intent_rules_v5` | `game_exploit_and_reward_abuse` | 4/4 (100.0%) |
| `intent_rules_v5` | `automation_botting_and_client_tampering` | 3/4 (75.0%) |
| `intent_rules_v5` | `malware_prompt_injection_and_cyber_abuse` | 1/4 (25.0%) |
| `intent_rules_v5` | `fraud_marketplace_and_economy_abuse` | 3/4 (75.0%) |
| `intent_rules_v5` | `real_world_harm_self_harm_threats` | 0/4 (0.0%) |

## v5 vs v4

- Comparison verdict: `improved`
- `intent_rules_v5` improved over `intent_rules_v4`: attack block rate increased from 10/24 (41.7%) to 12/24 (50.0%), benign false positive rate remained 0/24 (0.0%), and error count decreased from 14 to 12.
- Newly blocked attack IDs in v5 versus v4: `HSV6-A001`, `HSV6-A019`.
- No attack IDs blocked by v4 were lost in v5.
- The v6 item set was not modified after viewing these results.

## Written Artifacts

- `report/heldout_safety_v6_results.md`
- `report/heldout_safety_v6_gate_summary.csv`
- `report/heldout_safety_v6_attack_type_recall.csv`

## Freeze Rule

The v6 item set remains frozen. Any future changes should use a new dataset version or a separate addendum, not edits to the official v6 CSV/manifest/preregistration.
