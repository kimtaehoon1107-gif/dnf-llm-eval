# Held-out Safety v6 Final Verification Declaration

Created: 2026-07-03

## Declaration

`heldout_safety_v6` is pre-declared as the final fresh blind verification set for this safety-gate improvement round.

The v6 result will be included in the final report as-is, regardless of whether `intent_rules_v5` improves, ties, or regresses compared with prior gates.

## Freeze Basis

- freeze commit: `fd99061b9c6b309a9034d9f0cf57ea5d44a223f4`
- CSV: `questions/heldout_safety_v6.csv`
- CSV sha256: `bce8f120af1776736428b092ebd96f126eb39b75563f2cecec4e2a57fe9980b1`
- row count: 48
- attack / benign: 24 / 24

## Evaluation To Run

The final v6 evaluation compares:

- `keyword_rules_v2`
- `intent_rules_v4`
- `intent_rules_v5`

Metrics:

- attack block rate
- benign false positive rate
- attack-type recall
- dry-run error count

## Reporting Rule

After v6 results are viewed:

- do not edit `heldout_safety_v6.csv`
- do not edit `heldout_safety_v6.manifest.json`
- do not edit `report/heldout_safety_v6_preregistration.md`
- do not change gate rules before writing the final report
- do not create another fresh blind set for this same improvement round
- report v6 as the final blind verification outcome, even if the result is negative or inconclusive

Development regression results from `safety_regression_v2` through `safety_regression_v5` may be used only as development context. They must not replace the v6 blind result.

## Completion Criterion

This round can be closed after:

1. the frozen v6 evaluation is completed and committed,
2. the final report records the v6 result without post-result tuning,
3. any future work is explicitly started as a new improvement round rather than as a continuation of this verification claim.
