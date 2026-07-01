# Structured Record Diagnostic Probe v1

Date: 2026-07-02

## Status

This is not a new blind held-out set.

The existing `heldout_factual_v1` result remains preserved as the audit result:

- blind held-out factual set: 25 questions
- structured record firing: 0/25
- ablation scores: 23/25 across no-structured, structured records, and structured fix
- interpretation: hand-authored records did not transfer to blind new questions

This file reports a separate diagnostic/probe experiment. Its purpose is narrower:

> When a structured record actually fires, does structured data improve answer quality?

Because this probe intentionally targets the existing structured records, it must not be used as held-out generalization evidence.

## Probe Design

Question file: `questions/structured_record_probe_v1.csv`

Manifest: `questions/structured_record_probe_v1.manifest.json`

Rows: 35

Record firing dry run:

- matched rows: 25/35
- unique structured records fired: 7/7
- controls and near-miss rows were included to check whether matching becomes too broad

Covered structured records:

- `DNF-2927691-CHANGE-01`
- `DNF-2927756-CHANGE-01`
- `DNF-2927756-CHANGE-02`
- `DNF-2927810-CHANGE-01`
- `DNF-2927810-SHOP-01`
- `DNF-2927810-SHOP-02`
- `DNF-2927822-CHANGE-01`

Question groups:

- target direct: asks directly about a structured record
- target paraphrase: asks with different wording around the same record
- target completeness: asks for before/after/unchanged or multi-field completeness
- near-miss same-doc: same source document, but should not need the record
- near-miss over-trigger: intentionally broad question to expose broad matching
- control no-record: documents without structured records

## Conditions

All runs used `qwen3:4b-instruct-2507-q4_K_M`, hybrid retrieval, `--num-ctx 8192`, `--num-predict 512`, and `--disable-thinking`.

| Condition | Meaning |
| --- | --- |
| `probe_no_structured` | baseline RAG, no structured records |
| `probe_atomic_records` | structured data on, but `source_relation` and completeness rules disabled |
| `probe_structured_fix` | full structured fix: records, source relation, and completeness rules |

## Summary Result

| Condition | Factual proxy | Format proxy | Refusals | Avg latency |
| --- | ---: | ---: | ---: | ---: |
| `probe_no_structured` | 24/35 | 35/35 | 2 | 4.543s |
| `probe_atomic_records` | 30/35 | 35/35 | 0 | 4.524s |
| `probe_structured_fix` | 32/35 | 35/35 | 0 | 4.729s |

Main result:

- atomic structured records improved factual proxy from 24/35 to 30/35
- full structured fix improved further to 32/35
- refusals dropped from 2 to 0 when structured records were enabled

This answers the probe question: under record-firing conditions, structured data does help.

## Breakdown

| Question group | No structured | Atomic records | Structured fix |
| --- | ---: | ---: | ---: |
| target change completeness | 3/5 | 5/5 | 5/5 |
| target change direct | 3/5 | 4/5 | 5/5 |
| target change paraphrase | 2/5 | 3/5 | 4/5 |
| target shop direct | 1/2 | 2/2 | 2/2 |
| target shop paraphrase | 2/2 | 2/2 | 2/2 |
| target shop completeness | 1/2 | 1/2 | 1/2 |
| near-miss same-doc | 6/6 | 6/6 | 6/6 |
| near-miss over-trigger | 2/2 | 2/2 | 2/2 |
| control no-record | 3/4 | 3/4 | 3/4 |

The gain is concentrated in target change records, especially completeness/direct/paraphrase questions. This is consistent with the intended role of structured records: they make before/after/unchanged fields explicit and reduce omission.

The near-miss and control groups were mostly stable. The over-trigger rows did fire by design, but did not reduce factual proxy in this probe. They should still be treated as matching-risk diagnostics, not as proof that broad matching is always harmless.

## Failure Notes

Persistent failures in `probe_structured_fix`:

- `SRP006`: the model answered that the purchase limit is "none", while the gold answer says the evidence does not provide purchase-limit information. This reveals a missing-field semantics issue: the structured shop record can encode `purchase_limit: none`, but the evidence/gold treats the field as not confirmed.
- `SRP014`: the model answer appears semantically correct, but the proxy scorer marked it as failed. This should be reviewed as a likely proxy false negative.
- `SRP033`: the model answered the total omitted gates as 3, but omitted the "1 gate added" part required by gold. This is a completeness-sensitive control failure.

Notable baseline failures:

- `SRP018`, `SRP020`, and `SRP035` were answered as not found by `probe_no_structured`, while structured records supplied the needed Breaker option details.
- `SRP007` and `SRP009` show baseline omission or awkward completeness handling around "Prime Stella 10 -> no material cost" and unchanged experience cost.

## Interpretation

This probe does not overturn the held-out audit. It complements it.

The combined conclusion is:

1. Blind held-out v1 showed that hand-authored records did not transfer to new questions because no held-out question triggered a record.
2. This diagnostic probe shows that, when records do trigger, structured fields improve answer quality.

Therefore, the next research problem is not "add more hand-written hints." The next problem is record coverage and record generation:

- can records be generated from source patch notes before seeing benchmark questions?
- can a blind or automatic extractor create atomic before/after/unchanged fields that fire on new questions?
- can matching be made broad enough to cover paraphrases without over-triggering unrelated questions?

In portfolio wording, this should be framed as:

> The held-out audit found non-transfer of hand-authored records; the diagnostic probe then isolated the mechanism and showed that structured records are useful when they fire. The remaining bottleneck is record coverage/extraction, not the structured answer mechanism itself.

## Artifacts

- `questions/structured_record_probe_v1.csv`
- `questions/structured_record_probe_v1.manifest.json`
- `eval/structured_record_probe_v1_no_structured_answers.csv`
- `eval/structured_record_probe_v1_no_structured_answers.manifest.json`
- `eval/structured_record_probe_v1_atomic_records_answers.csv`
- `eval/structured_record_probe_v1_atomic_records_answers.manifest.json`
- `eval/structured_record_probe_v1_structured_fix_answers.csv`
- `eval/structured_record_probe_v1_structured_fix_answers.manifest.json`
- `eval/structured_record_probe_v1_summary.csv`
- `eval/structured_record_probe_v1_detail.csv`
