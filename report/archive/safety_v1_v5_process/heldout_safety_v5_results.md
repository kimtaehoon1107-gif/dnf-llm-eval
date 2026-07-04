# Held-out Safety v5 Results

## Freeze and Integrity

- Freeze commit: `c364d80` (`c364d80a48cdab316c0b5e4b45a87cac3b191e00`)
- CSV: `questions/heldout_safety_v5.csv`
- CSV sha256: `1a0fcdc4ef2b89da0d66960f2cf18a1e950e34e3a30268645ba2ff9a78e5dd97`
- Manifest: `questions/heldout_safety_v5.manifest.json`
- Preregistration: `report/heldout_safety_v5_preregistration.md`
- Row count / attack_count / benign_count: 48 / 24 / 24
- CSV/manifest/preregistration modified: no
- Gate implementation modified: no
- Official v5 CSV modified after results: no
- Dry-run errors: no (`dry_run_error_count=0` for all three runs)

The actual CSV hash matched the manifest hash before evaluation. The target CSV, manifest, and preregistration had no git status changes before result writing and were not edited after results were viewed.

## Gate Metrics

| Gate | Mode | Rules commit | Attack block rate | Benign FP rate | Error count | Dry-run errors |
|---|---|---:|---:|---:|---:|---:|
| `keyword_rules_v2` | `keyword` | `c364d80` | 2/24 (8.3%) | 0/24 (0.0%) | 22 | 0 |
| `intent_rules_v3` | `intent` | `f50a2fa` | 8/24 (33.3%) | 0/24 (0.0%) | 16 | 0 |
| `intent_rules_v4` | `intent` | `c364d80` | 8/24 (33.3%) | 0/24 (0.0%) | 16 | 0 |

Error count is `false_negative_count + false_positive_count`, where unblocked attack rows are false negatives and blocked benign rows are false positives.

## Attack Type Recall

Attack type labels are analysis-only groupings derived from the frozen `gold_answer`/request-intent text; the CSV was not edited to add labels.

| Gate | Attack type | Recall |
|---|---|---:|
| `keyword_rules_v2` | `access_or_limit_bypass` | 0/4 (0.0%) |
| `keyword_rules_v2` | `automation_abuse` | 2/3 (66.7%) |
| `keyword_rules_v2` | `data_or_privacy_abuse` | 0/4 (0.0%) |
| `keyword_rules_v2` | `exploit_or_manipulation` | 0/5 (0.0%) |
| `keyword_rules_v2` | `security_evasion` | 0/1 (0.0%) |
| `keyword_rules_v2` | `service_disruption_or_griefing` | 0/2 (0.0%) |
| `keyword_rules_v2` | `social_engineering_or_fraud` | 0/5 (0.0%) |
| `intent_rules_v3` | `access_or_limit_bypass` | 3/4 (75.0%) |
| `intent_rules_v3` | `automation_abuse` | 2/3 (66.7%) |
| `intent_rules_v3` | `data_or_privacy_abuse` | 1/4 (25.0%) |
| `intent_rules_v3` | `exploit_or_manipulation` | 2/5 (40.0%) |
| `intent_rules_v3` | `security_evasion` | 0/1 (0.0%) |
| `intent_rules_v3` | `service_disruption_or_griefing` | 0/2 (0.0%) |
| `intent_rules_v3` | `social_engineering_or_fraud` | 0/5 (0.0%) |
| `intent_rules_v4` | `access_or_limit_bypass` | 3/4 (75.0%) |
| `intent_rules_v4` | `automation_abuse` | 2/3 (66.7%) |
| `intent_rules_v4` | `data_or_privacy_abuse` | 1/4 (25.0%) |
| `intent_rules_v4` | `exploit_or_manipulation` | 2/5 (40.0%) |
| `intent_rules_v4` | `security_evasion` | 0/1 (0.0%) |
| `intent_rules_v4` | `service_disruption_or_griefing` | 0/2 (0.0%) |
| `intent_rules_v4` | `social_engineering_or_fraud` | 0/5 (0.0%) |

## v3 vs v4

- Comparison verdict: `tie`
- intent_rules_v4 tied intent_rules_v3: both blocked 8/24 attack rows, blocked 0/24 benign rows, and produced the same blocked attack IDs.
- No v5 questions were changed after checking this result.

## Dry-run Outputs

- `keyword_rules_v2`: `eval/heldout_safety_v5_keyword_rules_v2_dry_run.csv`
- `intent_rules_v3`: `eval/heldout_safety_v5_intent_rules_v3_dry_run.csv`
- `intent_rules_v4`: `eval/heldout_safety_v5_intent_rules_v4_dry_run.csv`

## Written Artifacts

- `report/heldout_safety_v5_results.md`
- `report/heldout_safety_v5_gate_summary.csv`
- `report/heldout_safety_v5_attack_type_recall.csv`

## Freeze Rule

The v5 item set remains frozen. Any future changes should use a new dataset version or a separate amendment, not edits to the official v5 CSV/manifest/preregistration.
