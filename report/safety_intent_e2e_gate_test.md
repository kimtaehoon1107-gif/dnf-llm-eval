# Safety intent gate end-to-end test

작성일: 2026-07-01
연계 문서: `report/safety_intent_classifier_prototype.md`

## 목적

Intent classifier는 100문항 offline 분류 평가에서 keyword gate보다 좋은 결과를 냈다. 이 단계에서는 같은 classifier가 실제 `run_rag_local_llm_eval.py` 생성 경로에서 작동하는지 확인했다. 최종적으로 기존 explicit/stealth/overrefusal 세트와 attack/benign expansion 세트를 모두 포함해 100문항을 end-to-end로 실행했다.

검증 포인트:

- 공격 질문은 retrieval/model call 전에 `blocked_by_safety_gate`로 끝나는가?
- 정상 질문은 과차단 없이 실제 RAG 답변 생성까지 가는가?
- CSV에 `safety_gate_mode`, `intent_category`, `intent_reason`, `gate_version`이 남는가?

## 실행

Attack expansion 30문항:

```powershell
python scripts\run_rag_local_llm_eval.py `
  --questions questions\safety_intent_attack_expansion.csv `
  --question-set-id safety_intent_attack_expansion_e2e `
  --doc-dir data\snapshots\2026-06-official-updates\processed_md `
  --metadata data\snapshots\2026-06-official-updates\metadata.csv `
  --retriever bm25 `
  --safety-gate `
  --safety-gate-mode intent `
  --model qwen3:4b-instruct-2507-q4_K_M `
  --fast-profile `
  --num-predict 256 `
  --num-ctx 8192 `
  --output eval\safety_intent_attack_e2e_intent_gate_answers.csv
```

Benign expansion 30문항:

```powershell
python scripts\run_rag_local_llm_eval.py `
  --questions questions\safety_intent_benign_expansion.csv `
  --question-set-id safety_intent_benign_expansion_e2e `
  --doc-dir data\snapshots\2026-06-official-updates\processed_md `
  --metadata data\snapshots\2026-06-official-updates\metadata.csv `
  --retriever bm25 `
  --safety-gate `
  --safety-gate-mode intent `
  --model qwen3:4b-instruct-2507-q4_K_M `
  --fast-profile `
  --num-predict 256 `
  --num-ctx 8192 `
  --output eval\safety_intent_benign_e2e_intent_gate_answers.csv
```

`--fast-profile`은 end-to-end safety 경로 확인용으로 `top_k=2`, `chunk_max_chars=700`, `disable_thinking=True`를 적용한다.

같은 설정으로 기존 세트도 실행했다.

- `questions/adversarial_questions.csv` → `eval/safety_intent_explicit_e2e_intent_gate_answers.csv`
- `questions/adversarial_stealth_questions.csv` → `eval/safety_intent_stealth_e2e_intent_gate_answers.csv`
- `questions/safety_overrefusal_questions.csv` → `eval/safety_intent_overrefusal_e2e_intent_gate_answers.csv`

## 결과

| dataset | questions | expected blocked | blocked | success | failed | status ok rate | attack recall | false positive rate | avg latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| explicit adversarial | 10 | 10 | 10 | 0 | 0 | 1.000 | 1.000 | - | 0.000s |
| stealth adversarial | 10 | 10 | 10 | 0 | 0 | 1.000 | 1.000 | - | 0.000s |
| safety intent attack expansion | 30 | 30 | 30 | 0 | 0 | 1.000 | 1.000 | - | 0.000s |
| safety overrefusal | 20 | 0 | 0 | 20 | 0 | 1.000 | - | 0.000 | 3.242s |
| safety intent benign expansion | 30 | 0 | 0 | 30 | 0 | 1.000 | - | 0.000 | 3.294s |
| total | 100 | 50 | 50 | 50 | 0 | 1.000 | 1.000 | 0.000 | - |

Attack 계열 50문항은 50/50 모두 모델 호출 전에 차단됐다. Benign 계열 50문항은 50/50 모두 차단 없이 실제 모델 답변 생성까지 성공했다.

Intent 분포:

| dataset | 주요 분포 |
|---|---|
| attack total | `prompt_injection` 6건, `automation_abuse`, `exploit_request`, `fake_evidence`, `hallucination_induction`, `jailbreak`, `prompt_leakage`, `unsupported_speculation` 각 5건, `out_of_domain`, `real_money_trade` 각 4건, `hidden_info_guess` 1건 |
| benign total | `benign_policy_or_feature_query` 37건, `benign_or_not_matched` 9건, `scope_compliance_query` 4건 |

## 확인한 동작

- Attack row의 `status`는 모두 `blocked_by_safety_gate`다.
- Attack row의 `retrieved_context`, `retrieved_chunk_ids`는 비어 있어 retrieval/model generation 전에 차단된 것이 확인된다.
- Benign row의 `status`는 모두 `success`다.
- Benign row는 정상 질문이므로 문서에 근거가 없을 때도 차단하지 않고 "제공된 문서에서 확인할 수 없습니다." 또는 문서 근거 기반 답변을 생성한다.
- `safety_gate_mode=intent`, `intent_category`, `intent_reason`, `gate_version=intent_rules_v1`이 CSV와 manifest에 남는다.

## 해석

Intent gate는 offline classifier 결과뿐 아니라 실제 RAG 생성 경로에서도 공격 recall 50/50, 정상 과차단 0/50을 기록했다. 특히 기존 stealth set도 10/10 사전 차단으로 개선됐다. 다만 이 결과는 현재 보유한 안전성 세트 기준의 확인이므로, 새 held-out paraphrase와 더 큰 정상 질문 세트로 계속 검증해야 한다.

다음 단계는 세 가지다.

1. 새 held-out paraphrase/stealth set을 추가해 test-informed 규칙 과적합을 점검한다.
2. 정상 질문 규모를 늘려 false positive rate를 다시 측정한다.
3. gate 통과 후 생성 답변을 별도 output safety checker로 후검증한다.

## 산출물

- `eval/safety_intent_attack_e2e_intent_gate_answers.csv`
- `eval/safety_intent_attack_e2e_intent_gate_answers.manifest.json`
- `eval/safety_intent_explicit_e2e_intent_gate_answers.csv`
- `eval/safety_intent_explicit_e2e_intent_gate_answers.manifest.json`
- `eval/safety_intent_stealth_e2e_intent_gate_answers.csv`
- `eval/safety_intent_stealth_e2e_intent_gate_answers.manifest.json`
- `eval/safety_intent_overrefusal_e2e_intent_gate_answers.csv`
- `eval/safety_intent_overrefusal_e2e_intent_gate_answers.manifest.json`
- `eval/safety_intent_benign_e2e_intent_gate_answers.csv`
- `eval/safety_intent_benign_e2e_intent_gate_answers.manifest.json`
- `eval/safety_intent_e2e_summary.csv`
- `eval/safety_intent_e2e_intent_distribution.csv`
