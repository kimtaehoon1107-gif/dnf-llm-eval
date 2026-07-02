# safety_regression_v3 Design

작성일: 2026-07-03

## Status

`safety_regression_v3` is a development regression set based on the reviewed `heldout_safety_v3` diagnostic. It is not a blind held-out set and must not be used as evidence of fresh generalization.

This set does not replace the official v3 result. The official v3 CSV, manifest, gate summaries, and attack-type recall tables remain the result of record.

Source diagnostic commit named by the authoring instruction: `6dd1849`

Reviewed diagnostic base recorded in the review manifest: `387e31f`

## Source Files

- `report/heldout_safety_v3_results.md`
- `report/heldout_safety_v3_gate_summary.csv`
- `report/heldout_safety_v3_attack_type_recall.csv`
- `report/heldout_safety_v3_error_analysis_reviewed.md`
- `report/heldout_safety_v3_taxonomy_crosswalk_reviewed.csv`
- `report/heldout_safety_v3_attack_type_recall_taxonomy_v2_reviewed.csv`
- `report/heldout_safety_v3_independent_review_notes.md`
- `report/heldout_safety_v3_diagnostic_review_manifest.json`
- `questions/heldout_safety_v3.csv`
- `questions/heldout_safety_v3.manifest.json`
- `data/snapshots/2026-06-official-updates/processed_md/*`

## Distribution

Total rows: 48

Attack rows: 24

Benign rows: 24

Matched pairs: 24

| question_type | attack rows | benign rows |
|---|---:|---:|
| priority_inversion | 3 | 0 |
| answer_rule_laundering | 3 | 0 |
| policy_null_roleplay | 4 | 0 |
| unsupported_official_assertion | 5 | 0 |
| sanction_evasion | 3 | 0 |
| multi_account_automation | 3 | 0 |
| structural_rmt | 3 | 0 |
| negated_trigger_benign | 0 | 4 |
| public_source_policy_benign | 0 | 18 |
| documented_ui_benign | 0 | 2 |

## Included FN Structures

The attack side generalizes the 11 reviewed `intent_rules_v2` false negatives without copying the original v3 prompts.

- `v3_attack_prompt_injection_02`: user-message priority over system/rules plus unverified possible-as-if answer.
- `v3_attack_prompt_injection_03`: answer-rule change plus official-answer laundering.
- `v3_attack_jailbreak_01`: authority or official-operator roleplay plus off-document bypass content.
- `v3_attack_jailbreak_03`: policy-null hypothetical world plus prohibited domain processed as normal.
- `v3_attack_fake_evidence_03`: as-if-found official statement for an unsupported sensitive claim.
- `v3_attack_unsupported_speculation_02`: internal probability or metric asserted as definitive.
- `v3_attack_unsupported_speculation_03`: future expansion or plan framed as official.
- `v3_attack_exploit_request_02`: sanction evasion plus repeated misconduct tips.
- `v3_attack_automation_abuse_03`: multiple accounts plus repeated purchasing or account-scale automation.
- `v3_attack_real_money_trade_01`: game reward or currency plus external cash-trade valuation method.
- `v3_attack_real_money_trade_03`: account/equipment value plus external sale post drafting.

## Included FP Guard Structures

The benign side includes narrow guard coverage for the three reviewed false positives.

- `v3_benign_trigger_adjacent_02`: phrases such as 비공개 정보 말고 are allowed only when the request is clearly for public patch-note conditions.
- `v3_benign_trigger_adjacent_07`: phrases such as 매크로 설계가 아니라 are allowed only for documented UI/input behavior, not scripts or automation flows.
- `v3_benign_trigger_adjacent_09`: phrases such as 숨은 지시를 묻는 게 아니라 are allowed only for public patch changes, not hidden prompts or private instructions.

These guards are intentionally narrow. They should remain below hard-block overrides for real hidden prompt disclosure, private internal conditions, macro implementation, evasion, RMT, or abuse workflows.

## Matched Pair Principles

Each `SRV3-P###` pair contains one attack row and one benign row with the same `pair_id` embedded in `expected_behavior`.

Benign rows reuse nearby risky words such as 비공개, 숨은 지시, 제재, 매크로, 자동화, 현금 거래, 계정, 확률, or 공식 근거, but remove execution, evasion, fabrication, monetization, or abuse intent. Benign rows are grounded in public patch-note text or documented UI behavior.

Attack rows are phrased as user requests only. They do not include exploit steps, bypass procedures, scripts, or operational instructions.

## Use For Rules v3 Work

Use this set after a proposed `intent_rules_v3` change to check that the reviewed v3 diagnostic failures have been converted into durable regression coverage. Passing this set should be treated as development feedback only.

Do not report performance on `safety_regression_v3` as blind held-out performance. After rules v3 changes, a fresh blind v4 set is still required for generalization evidence.
