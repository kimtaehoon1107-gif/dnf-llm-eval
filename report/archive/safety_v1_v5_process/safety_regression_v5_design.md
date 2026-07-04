# safety_regression_v5 Design

작성일: 2026-07-03

## Status

`safety_regression_v5` is a development regression set based on the reviewed `heldout_safety_v5` diagnostic. It is not a strict blind held-out set and must not be used as fresh generalization evidence.

This set does not replace the official v5 result. The official `heldout_safety_v5` question CSV, manifest, dry-run output, gate summary, attack-type recall, and result report remain the result of record.

Source diagnostic commit named by the authoring instruction: `7c302a1`

Reviewed diagnostic base recorded in the review manifest: `b68ec4e`

## Source Files

- `report/heldout_safety_v5_error_analysis_reviewed.md`
- `report/heldout_safety_v5_taxonomy_crosswalk_reviewed.csv`
- `report/heldout_safety_v5_attack_type_recall_taxonomy_v2_reviewed.csv`
- `report/heldout_safety_v5_independent_review_notes.md`
- `report/heldout_safety_v5_diagnostic_review_manifest.json`
- `questions/heldout_safety_v5.csv`
- `questions/heldout_safety_v5.manifest.json`
- `data/processed_md/*`
- `data/snapshots/2026-06-official-updates/processed_md/*`

## Distribution

Total rows: 48

Attack rows: 24

Benign rows: 24

Matched pairs: 24

| question_type | attack rows | benign rows |
|---|---:|---:|
| credential_theft_or_phishing | 3 | 0 |
| trade_scam_or_market_fraud | 3 | 0 |
| client_or_reward_manipulation | 3 | 0 |
| data_exfiltration_or_doxxing | 3 | 0 |
| security_detection_evasion | 3 | 0 |
| service_disruption_or_griefing | 3 | 0 |
| access_or_limit_bypass | 3 | 0 |
| automation_or_spam_abuse | 3 | 0 |
| public_reward_price_purchase_limit_benign | 0 | 8 |
| otp_security_guidance_benign | 0 | 2 |
| first_server_update_notice_benign | 0 | 6 |
| report_channel_benign | 0 | 3 |
| dungeon_condition_hp_time_limit_benign | 0 | 5 |

## Included FN Structures

The attack side generalizes the reviewed `intent_rules_v4` v5 false negatives without copying exploit steps or providing operational instructions. Each attack row is written as a request-intent sentence only.

- `credential_theft_or_phishing`: reward-context credential phishing, OTP harvesting by unlock impersonation, and NPC/reward malicious-link lures.
- `trade_scam_or_market_fraud`: in-game trade deception and market-price deception without RMT wording.
- `client_or_reward_manipulation`: abnormal time/progress manipulation, reward probability or false-display manipulation, and client-side HP tampering.
- `data_exfiltration_or_doxxing`: unauthorized update-data extraction, secret collection of another user's account or inventory data, and doxxing after party conflict.
- `security_detection_evasion`: hiding client or account manipulation from security detection.
- `service_disruption_or_griefing`: forced party failure, time-limit griefing, and traffic-based service disruption.
- `access_or_limit_bypass`: entry eligibility spoofing and related documented entry or purchase-limit bypass intent.
- `automation_or_spam_abuse`: mass false-report automation and report-channel spam abuse.

## Included FP Guard Structures

The official v5 run had 0 benign false positives, so the benign side is trigger-adjacent and intentionally public-document grounded:

- Public reward, price, item-use, market notice, and purchase-limit questions.
- Normal OTP/security notice questions.
- First-server and update-notice questions.
- Normal report or feedback channel questions.
- Dungeon entry condition, HP, time-limit, weekly-limit, and failure-condition questions.

These guards are designed so future rules do not overblock words such as 보상, 가격, 구매 제한, OTP, 퍼스트 서버, 게시판, 신고, 입장 명성, 제한 시간, HP, 탐지, 자동화, or 조작 when the user is asking only for public official-document facts.

## Matched Pair Principles

Each `SRV5-P###` pair contains one attack row and one benign row with the same `pair_id` embedded in `expected_behavior`.

The benign row deliberately shares nearby vocabulary with the paired attack row but removes credential theft, deception, manipulation, exfiltration, evasion, disruption, bypass, spam, or automation-abuse intent. Benign answers must be grounded in public official update documents only.

## Use For Rules v5 Work

Use `safety_regression_v5` as a development regression set after proposed rules v5 changes to check whether reviewed v5 failure structures have been converted into regression coverage while preserving trigger-adjacent public-document behavior.

Do not run or report this set as a fresh blind evaluation. It was authored after viewing the official v5 result and the independent reviewed diagnostic.

No gate implementation files were modified while authoring this set. No official `heldout_safety_v5` result artifacts were modified.
