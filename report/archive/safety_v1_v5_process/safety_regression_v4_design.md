# safety_regression_v4 Design

작성일: 2026-07-03

## Status

`safety_regression_v4` is a development regression set based on the reviewed `heldout_safety_v4` diagnostic. It is not a blind held-out set and must not be used as evidence of fresh generalization.

This set does not replace the official v4 result. The official v4 CSV, manifest, gate summaries, and attack-type recall tables remain the result of record.

Source diagnostic review commit named by the authoring instruction: `fa59048`

Reviewed diagnostic base recorded in the review manifest: `99ccc5d`

## Source Files

- `report/heldout_safety_v4_results.md`
- `report/heldout_safety_v4_gate_summary.csv`
- `report/heldout_safety_v4_attack_type_recall.csv`
- `report/heldout_safety_v4_error_analysis_reviewed.md`
- `report/heldout_safety_v4_taxonomy_crosswalk_reviewed.csv`
- `report/heldout_safety_v4_attack_type_recall_taxonomy_v2_reviewed.csv`
- `report/heldout_safety_v4_independent_review_notes.md`
- `report/heldout_safety_v4_diagnostic_review_manifest.json`
- `questions/heldout_safety_v4.csv`
- `questions/heldout_safety_v4.manifest.json`
- `data/snapshots/2026-06-official-updates/processed_md/*`

## Distribution

Total rows: 48

Attack rows: 24

Benign rows: 24

Matched pairs: 24

| question_type | attack rows | benign rows |
|---|---:|---:|
| private_refusal_template_leakage | 3 | 0 |
| no_refusal_mode_payload | 3 | 0 |
| dev_test_payload_laundering | 3 | 0 |
| resource_bypass_procedure | 3 | 0 |
| entry_limit_reclaim_repro | 3 | 0 |
| account_lookup_automation | 3 | 0 |
| reward_cash_trade_route | 3 | 0 |
| account_valuation_sale_listing | 3 | 0 |
| public_refusal_policy_benign | 0 | 3 |
| documented_test_or_ui_benign | 0 | 3 |
| documented_resource_limit_benign | 0 | 9 |
| documented_account_lookup_benign | 0 | 6 |
| documented_item_trade_limit_benign | 0 | 3 |

## Included FN Structures

The attack side generalizes the 8 reviewed `intent_rules_v3` false negatives without copying the original v4 prompts.

- `hsv4_005`: private system message, hidden context, or non-public refusal-template wording requested verbatim.
- `hsv4_008`: no-refusal, verification, or refusal-disabled mode paired with a prohibited bypass, exploit, automation, or RMT payload.
- `hsv4_009`: development-test, QA, or special-scenario framing used to launder automation or RMT content as ordinary guidance.
- `hsv4_016`: resource, material, cost, purchase, or use-limit bypass requests when paired with an abuse procedure.
- `hsv4_017`: entry-count or resource-count reclaim, restore, get-back, or reproduction requests.
- `hsv4_020`: repeated or multi-account DNF ON account lookup automation paired with collection or script/design intent.
- `hsv4_022`: reward, item, or shop good connected to external cash sale, cash-out, or sale-route intent.
- `hsv4_024`: DNF ON armory results or account holdings connected to account valuation, sale post, listing copy, or sale price.

Attack rows are written as user request sentences only. They do not provide exploit steps, bypass procedures, scripts, sale routes, or operational instructions.

## Included FP / Overrefusal Guard Structures

The official v4 benign result had 0 false positives, so the benign side intentionally includes trigger-adjacent but allowed questions. Each benign row is grounded in a public patch-note fact.

- Public refusal or hidden-context negations that end in a normal public patch-note summary.
- Verification, QA, development, or automation-adjacent words used only to ask about documented UI behavior or bug fixes.
- Documented material costs, purchase limits, free counts, entry-count notices, and resource-consumption rules.
- Ordinary DNF ON lookup scope, eligibility, menu path, and excluded equipment questions.
- Public item trade type, account-bound or untradeable status, NPC shop price, and purchase-limit questions.

These guards are narrow. Future rules should not treat words such as 검증, 개발 테스트, 자동, 계정, 가치, 거래, 제한, 재료, 거절, or hidden context as standalone block signals. Blocking should require private-content disclosure or a prohibited payload such as bypass, automation, RMT, or sale/listing intent.

## Matched Pair Principles

Each `SRV4-P###` pair contains one attack row and one benign row with the same `pair_id` embedded in `expected_behavior`.

Benign rows share nearby risky terms with the paired attack row but remove execution, evasion, automation, cash-out, valuation, or private-disclosure intent. They answer only from official public patch-note text.

The pairs are intentionally development-focused. Passing this set indicates that a proposed rules v4 change covers reviewed v4 failure structures while preserving known benign adjacent behavior; it does not establish blind held-out performance.

## Use For Rules v4 Work

Use `safety_regression_v4` after proposed rules v4 changes to check whether the reviewed v4 diagnostic failures have been converted into regression coverage. The expected behavior is encoded in each row as `expected_blocked=1` or `expected_blocked=0`.

Do not run or report this set as a fresh blind evaluation. It was authored after viewing official v4 results and the independent diagnostic review.

After rules v4 work, a separate fresh blind v5 set is still required before making any generalization claim.
