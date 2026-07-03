# Safety Gate Evaluation Final Report

Created: 2026-07-03

## Final Verification Rule

This round was closed under the pre-result declaration in `report/heldout_safety_v6_final_verification_declaration.md`.

- declaration commit: `ebe38a1`
- final fresh blind set: `heldout_safety_v6`
- freeze commit: `fd99061b9c6b309a9034d9f0cf57ea5d44a223f4`
- result commit: `8f1393c`
- CSV sha256: `bce8f120af1776736428b092ebd96f126eb39b75563f2cecec4e2a57fe9980b1`

The v6 result is reported as-is. No post-v6 gate tuning is part of this round.

## Final Blind Result

| gate | attack block rate | benign FP rate | error count |
|---|---:|---:|---:|
| keyword_rules_v2 | 1/24 (4.2%) | 0/24 (0.0%) | 23 |
| intent_rules_v4 | 10/24 (41.7%) | 0/24 (0.0%) | 14 |
| intent_rules_v5 | 12/24 (50.0%) | 0/24 (0.0%) | 12 |

Final verdict:

- `intent_rules_v5` improved over `intent_rules_v4` on the final fresh blind v6 set.
- Attack block rate improved by 2 rows: 10/24 -> 12/24.
- Benign false positive rate stayed at 0/24.
- No v4-blocked attack rows were lost in v5.

## Attack-Type View

| attack type | intent_rules_v4 | intent_rules_v5 |
|---|---:|---:|
| credential_phishing_privacy_harassment | 0/4 | 1/4 |
| game_exploit_and_reward_abuse | 4/4 | 4/4 |
| automation_botting_and_client_tampering | 3/4 | 3/4 |
| malware_prompt_injection_and_cyber_abuse | 1/4 | 1/4 |
| fraud_marketplace_and_economy_abuse | 2/4 | 3/4 |
| real_world_harm_self_harm_threats | 0/4 | 0/4 |

The measured improvement came from one additional credential/phishing/privacy-harassment row and one additional fraud/marketplace/economy-abuse row.

## Development Context

The development path before v6 was:

- v5 diagnostic review commit: `7c302a1`
- regression v5 set commit: `df97ac7`
- regression v5 baseline commit: `eed4e68`
- rules v5 update commit: `b802865`

Development regression results showed that `intent_rules_v5` covered `safety_regression_v5` at 24/24 attack recall and 0/24 benign FP, while preserving the earlier v2/v3/v4 regression checks. These regression results are development evidence only. They do not replace the final v6 blind verification.

## Integrity Notes

- `heldout_safety_v6.csv`, manifest, and preregistration were frozen before evaluation.
- v6 was declared the final fresh blind verification before result files were present.
- v6 CSV/manifest/preregistration were not edited after results were viewed.
- gate implementation was not modified during v6 evaluation or final reporting.
- no additional fresh blind set is used to revise this round's conclusion.

## Closure

This improvement round is complete.

Future changes should be treated as a new improvement round with a new preregistered development and blind-verification sequence. The v6 outcome above remains the final reported blind result for this round.
