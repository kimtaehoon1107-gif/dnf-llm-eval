# Held-out Safety v1 Results

작성일: 2026-07-02

## Freeze

- 질문셋: `questions/heldout_safety_v1.csv`
- Manifest: `questions/heldout_safety_v1.manifest.json`
- Freeze commit: `fc2e561` (`Freeze held-out safety set v1 (blind, pre-gate-eval)`)
- CSV sha256: `ca2a7a9541eab9f1ae40c22c13aedd182be380e160b8eca1c0aa0b7e15693d18`
- 구성: 공격 24문항, 정상 24문항

## Dry-run Gate Metrics

같은 frozen CSV에서 keyword gate와 intent gate를 각각 `--dry-run --safety-gate`로 실행했다.
Dry-run CSV는 저장소의 `.gitignore` 규칙(`eval/*dry_run*`)에 따라 로컬 중간 산출물로 남기고, 아래 표와 명령으로 재현 가능하게 기록한다.

| gate | attack blocked | attack recall | benign blocked | benign FP rate | output |
|---|---:|---:|---:|---:|---|
| keyword | 4/24 | 16.7% | 0/24 | 0.0% | `eval/heldout_safety_v1_keyword_gate_dry_run.csv` |
| intent | 6/24 | 25.0% | 0/24 | 0.0% | `eval/heldout_safety_v1_intent_gate_dry_run.csv` |

Intent gate는 keyword gate보다 attack recall이 높았지만, 절대 수치가 낮다. 따라서 intent 단독 수치를 headline으로 삼기보다 keyword baseline 대비 소폭 개선과 남은 실패 유형을 함께 보고한다.

## Attack Type Recall

| attack type | keyword | intent |
|---|---:|---:|
| automation_abuse | 1/3 | 1/3 |
| exploit_request | 0/3 | 0/3 |
| fake_evidence | 0/3 | 0/3 |
| jailbreak | 1/3 | 1/3 |
| prompt_injection | 0/3 | 3/3 |
| prompt_leakage | 0/3 | 0/3 |
| real_money_trade | 1/3 | 1/3 |
| unsupported_speculation | 1/3 | 0/3 |

가장 큰 차이는 prompt injection에서 intent gate가 3/3을 차단한 점이다. 반면 prompt leakage, fake evidence, exploit request는 held-out 새 문구에서 두 게이트 모두 사전 차단하지 못했다.

## Attack E2E Probe

공격 24문항만 대상으로 실제 Ollama 생성 단계까지 실행했다. 이 실행은 gate를 통과한 공격이 최종 답변 단계에서 거절되는지 보기 위한 보조 확인이다.

| gate | gate blocked | generated refusal proxy success | infra/model error | observed strict pass |
|---|---:|---:|---:|---:|
| keyword | 4 | 9 | 11 | 13/24 |
| intent | 6 | 8 | 10 | 14/24 |

주의: `failed` 행은 위험 답변이 생성된 것이 아니라 Ollama `HTTP Error 400: Bad Request`로 `model_answer`가 비어 있는 행이다. 따라서 strict pass 수치는 보수적으로 `gate blocked + generated success`만 세었고, error 행은 안전 성공으로 계산하지 않았다.

## Interpretation

- Intent gate는 held-out safety v1에서 keyword보다 attack recall이 높았다: 25.0% vs 16.7%.
- Benign FP rate는 두 게이트 모두 0.0%였다.
- 다만 held-out attack recall 자체가 낮아, intent gate의 일반화가 충분하다고 주장하기 어렵다.
- 특히 fake evidence와 exploit request는 blind 새 문구에 취약했다.
- 이 결과는 실패라기보다 기존 규칙이 dev 문장에 특화되었는지 드러내는 감사 결과로 해석한다.

## Commands

```powershell
python scripts\run_rag_local_llm_eval.py --questions questions\heldout_safety_v1.csv --question-set-id heldout_safety_v1 --doc-dir data\snapshots\2026-06-official-updates\processed_md --metadata data\snapshots\2026-06-official-updates\metadata.csv --retriever bm25 --dry-run --safety-gate --checked-at 2026-07-02 --output eval\heldout_safety_v1_keyword_gate_dry_run.csv

python scripts\run_rag_local_llm_eval.py --questions questions\heldout_safety_v1.csv --question-set-id heldout_safety_v1 --doc-dir data\snapshots\2026-06-official-updates\processed_md --metadata data\snapshots\2026-06-official-updates\metadata.csv --retriever bm25 --dry-run --safety-gate --safety-gate-mode intent --checked-at 2026-07-02 --output eval\heldout_safety_v1_intent_gate_dry_run.csv

python scripts\run_rag_local_llm_eval.py --questions questions\heldout_safety_v1.csv --question-set-id heldout_safety_v1_attacks_keyword_e2e --doc-dir data\snapshots\2026-06-official-updates\processed_md --metadata data\snapshots\2026-06-official-updates\metadata.csv --model qwen3:4b-instruct-2507-q4_K_M --retriever bm25 --limit 24 --safety-gate --checked-at 2026-07-02 --disable-thinking --num-predict 256 --timeout 120 --output eval\heldout_safety_v1_keyword_gate_attack_e2e_answers.csv

python scripts\run_rag_local_llm_eval.py --questions questions\heldout_safety_v1.csv --question-set-id heldout_safety_v1_attacks_intent_e2e --doc-dir data\snapshots\2026-06-official-updates\processed_md --metadata data\snapshots\2026-06-official-updates\metadata.csv --model qwen3:4b-instruct-2507-q4_K_M --retriever bm25 --limit 24 --safety-gate --safety-gate-mode intent --checked-at 2026-07-02 --disable-thinking --num-predict 256 --timeout 120 --output eval\heldout_safety_v1_intent_gate_attack_e2e_answers.csv
```
