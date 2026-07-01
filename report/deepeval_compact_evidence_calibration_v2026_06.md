# DeepEval compact evidence calibration for 2026-06

작성일: 2026-07-01
연계 문서: `report/structured_fix_iteration_v2026_06.md`

## 목적

Structured fix 이후 답변 CSV는 자동 factual proxy 20/20을 통과했다. 이 단계에서는 DeepEval faithfulness judge를 다시 실행하되, 기존 full RAG context 대신 compact evidence를 사용해 judge가 긴 context나 인접 표 행에 끌려가는지 확인했다.

## 변경 내용

`scripts/export_deepeval_rag_cases.py`에 context mode를 추가했다.

- `--context-mode full`: 기존 방식. 실제 prompt context를 block 단위로 분리한다.
- `--context-mode compact`: `structured_context`, `gold evidence`, top retrieved chunk를 합쳐 짧은 judge context를 만든다.
- `--compact-top-k`: compact mode에서 top retrieved chunk를 몇 개 붙일지 정한다.

Compact mode는 최종 retriever 성능을 재는 목적이 아니라 judge calibration용이다. 따라서 사람이 만든 `evidence`를 `[정답 기준 근거]` block으로 넣어, 답변이 최소 정답 근거에 의해 지지되는지 보는 데 초점을 둔다.

## 실행 결과

기준 답변:

- `eval/rag_v2026_06_hybrid_structured_fix_instruct_answers.csv`

Top-1 compact:

```powershell
python scripts\export_deepeval_rag_cases.py `
  --answers eval\rag_v2026_06_hybrid_structured_fix_instruct_answers.csv `
  --output eval\deepeval_rag_v2026_06_structured_fix_compact_cases.jsonl `
  --context-mode compact `
  --compact-top-k 1 `
  --fail-on-empty-context
```

```powershell
.venv\deepeval\Scripts\python.exe scripts\run_deepeval_rag_judge.py `
  --cases eval\deepeval_rag_v2026_06_structured_fix_compact_cases.jsonl `
  --metrics faithfulness `
  --judge-model qwen3:4b-instruct-2507-q4_K_M `
  --judge-num-ctx 8192 `
  --output eval\deepeval_rag_v2026_06_structured_fix_compact_faithfulness_judge.csv `
  --summary-output eval\deepeval_rag_v2026_06_structured_fix_compact_faithfulness_judge_summary.csv `
  --keep-going
```

Top-3 compact:

```powershell
python scripts\export_deepeval_rag_cases.py `
  --answers eval\rag_v2026_06_hybrid_structured_fix_instruct_answers.csv `
  --output eval\deepeval_rag_v2026_06_structured_fix_compact_top3_cases.jsonl `
  --context-mode compact `
  --compact-top-k 3 `
  --fail-on-empty-context
```

```powershell
.venv\deepeval\Scripts\python.exe scripts\run_deepeval_rag_judge.py `
  --cases eval\deepeval_rag_v2026_06_structured_fix_compact_top3_cases.jsonl `
  --metrics faithfulness `
  --judge-model qwen3:4b-instruct-2507-q4_K_M `
  --judge-num-ctx 8192 `
  --output eval\deepeval_rag_v2026_06_structured_fix_compact_top3_faithfulness_judge.csv `
  --summary-output eval\deepeval_rag_v2026_06_structured_fix_compact_top3_faithfulness_judge_summary.csv `
  --keep-going
```

| setting | context blocks avg | faithfulness pass | avg score | errors |
|---|---:|---:|---:|---:|
| compact top-1 | 2.45 | 12 / 20 | 0.690 | 0 |
| compact top-3 | 4.45 | 14 / 20 | 0.735 | 0 |

Top-3가 top-1보다 안정적이다. Top-1은 너무 좁아서 Q005, Q009, Q013처럼 답변은 맞지만 judge가 근거 일부를 놓치는 사례가 있었다. Top-3에서는 이 세 문항이 통과했다.

## 남은 fail 수동 판정

Top-3 compact fail 6건은 수동 리뷰에서 모두 생성 수정 대상이 아닌 judge calibration 대상으로 분류했다.

| QID | score | 수동 판정 | 이유 |
|---|---:|---|---|
| `Q003` | 0.000 | pass | 답변은 필요 재료 변경과 경험치 소모량 유지를 정확히 말한다. judge가 배경 조건 누락을 faithfulness 모순으로 과대평가했다. |
| `Q012` | 0.500 | pass | reason은 모순 없음과 score 1.00을 말하지만 기록 score는 0.500이다. |
| `Q016` | 0.000 | pass | reason은 답변이 context와 완전히 일치한다고 말하지만 기록 score는 0.000이다. |
| `Q017` | 0.000 | pass | 답변은 스택화 옵션 삭제와 적 추적 범위 증가를 말한다. judge가 이를 다른 변화로 오독했다. |
| `Q019` | 0.000 | pass | reason은 모순 없음과 score 1.00을 말하지만 기록 score는 0.000이다. |
| `Q020` | 0.500 | pass | reason은 모순 없음과 score 1.00을 말하지만 기록 score는 0.500이다. |

수동 리뷰 CSV:

- `eval/deepeval_rag_v2026_06_structured_fix_compact_top3_manual_review.csv`

## 결론

- Compact top-3를 DeepEval faithfulness triage의 기본 compact 설정으로 둔다.
- DeepEval faithfulness는 자동 최종 판정자가 아니라 manual review queue 정렬용으로 쓴다.
- 4B judge는 한국어 패치노트/게임 용어에서 self-consistency 오류가 남는다.
- `qwen3:8b` judge도 시도했지만 15분 제한 안에 완료되지 않아 이 환경의 기본 judge로 쓰기 어렵다.
- 다음 개선은 DeepEval 기본 faithfulness보다 custom GEval 또는 별도 rubric judge가 적합하다. 출력 JSON에 `factual_match`, `completeness`, `unsupported_addition`, `verdict`, `reason`을 강제하는 방식이 더 안정적이다.

## 산출물

- `eval/deepeval_rag_v2026_06_structured_fix_compact_cases.jsonl`
- `eval/deepeval_rag_v2026_06_structured_fix_compact_cases.manifest.json`
- `eval/deepeval_rag_v2026_06_structured_fix_compact_faithfulness_judge.csv`
- `eval/deepeval_rag_v2026_06_structured_fix_compact_faithfulness_judge_summary.csv`
- `eval/deepeval_rag_v2026_06_structured_fix_compact_top3_cases.jsonl`
- `eval/deepeval_rag_v2026_06_structured_fix_compact_top3_cases.manifest.json`
- `eval/deepeval_rag_v2026_06_structured_fix_compact_top3_faithfulness_judge.csv`
- `eval/deepeval_rag_v2026_06_structured_fix_compact_top3_faithfulness_judge_summary.csv`
- `eval/deepeval_rag_v2026_06_structured_fix_compact_top3_manual_review.csv`
