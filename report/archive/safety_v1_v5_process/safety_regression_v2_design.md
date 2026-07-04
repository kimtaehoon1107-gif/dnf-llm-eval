# safety_regression_v2 Design

This set is a targeted regression set informed by earlier safety evaluation results.
It is not claimed as a strict blind held-out set.

이 세트는 이전 평가 결과를 참고해 만든 targeted regression set이며, strict blind held-out으로 주장하지 않는다.

## Purpose

`safety_regression_v2` is for development and regression testing. It is designed after reviewing earlier safety results, so it should be used to harden gates and end-to-end refusal behavior rather than to make blind held-out claims.

## Basis From Earlier Results

The v2 gate dry-run showed low attack recall overall: keyword gate `33.3%`, intent gate `29.2%`, with `0.0%` benign false-positive rate in that run. The most important gaps were:

- complete misses on `exploit_request`
- complete misses on `fake_evidence`
- complete misses on `unsupported_speculation`
- weak or complete misses on `prompt_leakage`, especially for the intent gate

## Files

- `questions/safety_regression_v2.csv`
- `questions/safety_regression_v2.manifest.json`
- `report/safety_regression_v2_design.md`

In this Codex workspace, the deliverable bundle is written under `outputs/`.

## Schema

The CSV keeps the existing 8-column schema:

```text
question_id,doc_id,question_type,difficulty,question,gold_answer,evidence,expected_behavior
```

Every `expected_behavior` value starts with either:

```text
expected_blocked=1;
expected_blocked=0;
```

## Distribution

Total rows: 48

Attack rows: 24

Matched benign rows: 24

| question_type | attack rows | benign rows |
|---|---:|---:|
| prompt_leakage | 5 | 5 |
| fake_evidence | 5 | 5 |
| exploit_request | 5 | 5 |
| automation_abuse | 3 | 3 |
| real_money_trade | 2 | 2 |
| prompt_injection | 2 | 2 |
| jailbreak | 1 | 1 |
| unsupported_speculation | 1 | 1 |

Benign controls are split between plain patch questions and trigger-adjacent near-misses:

- `benign-patch-plain`: 10
- `benign-trigger-adjacent`: 14

## Matched Benign Design

Each attack row has a matched benign row with the same `pair_id` in `expected_behavior`. The benign row intentionally reuses nearby words such as threshold, 제재, 보상, 오류, 우회, 조회, 자동화, 근거, or jailbreak, but asks for a safe document-grounded, defensive, educational, or uncertainty-handling answer. This helps test whether the gate is learning intent instead of simply blocking adjacent vocabulary.

## Major Reinforcement Types

- `prompt_leakage`: hidden prompt, private threshold, retrieval context, developer note, safety-gate configuration disclosure.
- `fake_evidence`: fabricated official quotes, invented URLs, unsupported numeric limits, laundering user claims into official evidence.
- `exploit_request`: patch-note bug abuse, abnormal access, reward error, marketplace bug, restriction bypass.
- `automation_abuse`: abusive reward automation, enforcement evasion, account-scraping automation.
- `real_money_trade`: off-platform monetization and cash-trade promotion.
- `prompt_injection` and `jailbreak`: forged authority, instruction override, roleplay that removes safety limits.
- `unsupported_speculation`: future enforcement thresholds or probabilities stated as fact without documents.

## Validation

- 8 CSV columns parsed successfully.
- `row_count`: 48
- attack rows: 24
- matched benign rows: 24
- matched pair count: 24
- CSV SHA-256: `ffbba161414e128637aa0560a6bf473a0d961fc003bf5994feb2f743a6094b4d`

## Reporting Warning

Do not describe this set as a strict blind held-out set. It was intentionally authored with knowledge of earlier evaluation findings and should be used as a targeted safety regression set.
