# Claude Review Context: 2026-06 DNF RAG Evaluation

## Purpose

이 문서는 Codex와 진행한 `dnf-llm-eval` 작업 기록을 Claude에게 검토 요청하기 위해 정리한 handoff 문서다.

Claude에게 기대하는 역할은 다음과 같다.

- 2026-06 staged corpus 평가 결과 해석이 타당한지 검토
- RAG 개선 방향 중 무엇을 우선해야 하는지 조언
- 현재 token/phrase 기반 factual proxy가 놓치는 false negative를 어떻게 다룰지 제안
- patch-note 변경표를 structured record로 보강한 방식의 장단점 검토

## Repository State

- Local path: `C:\Users\kimdh\OneDrive\문서\New project 2`
- GitHub repo: `kimtaehoon1107-gif/dnf-llm-eval`
- Branch: `codex/v2026-06-results`
- Base commit used for this continuation: `4df4022 Add v2026_06 benchmark questions`
- Current latest commit: `5fff72b Add structured v2026_06 change records`

Recent commits:

```text
5fff72b Add structured v2026_06 change records
152f65a Add reranked v2026_06 evaluation run
d2f86bb Add v2026_06 retriever comparison results
4df4022 Add v2026_06 benchmark questions
```

## Conversation Flow Summary

1. 사용자가 Google Drive handoff 문서를 공유하며 local `dnf eval` repo와 연결해 달라고 요청했다.
2. Codex가 local repo를 GitHub `kimtaehoon1107-gif/dnf-llm-eval`와 연결하고 `main`을 checkout했다.
3. 사용자가 "이전과 달라진 거 있어?", "다음으로 진행할 건 뭐야?", "깃헙 issue #6 댓글도 봤어?"라고 물었다.
4. Codex가 GitHub Issue #6 댓글을 확인했다. 댓글 요지는 Ollama PC에서 2026-06 staged corpus 평가를 이어가야 하며, 실제 LLM 답변 생성은 아직 안 된 상태라는 것이었다.
5. 사용자가 "2026-06 결과 개선 실험으로 가보자"라고 했고, RAG 개선 방식 추천을 요청했다.
6. Codex는 BM25/BGE-M3/hybrid/rerank/structured data 후보를 제안했고, 우선 full-corpus hybrid와 reranker를 실행했다.
7. 이후 patch-note 변경표를 구조화 record로 보강하는 실험을 진행했다.
8. structured change records 적용 결과가 가장 좋은 자동 proxy 성능을 보였다.

## Implemented Changes

### 1. Ollama Context Window Option

File:

- `scripts/run_rag_local_llm_eval.py`

Change:

- `--num-ctx` 옵션 추가
- Ollama 기본 context 4096으로는 `top_k=8` RAG prompt 일부가 HTTP 400을 반환했기 때문에, 성공 실행에는 `--num-ctx 8192`를 사용했다.

### 2. 2026-06 Retriever And Generation Runs

Generated/updated outputs:

- `eval/rag_v2026_06_bm25_instruct_answers.csv`
- `eval/rag_v2026_06_bge_m3_instruct_answers.csv`
- `eval/rag_v2026_06_hybrid_instruct_answers.csv`
- `eval/rag_v2026_06_hybrid_rerank_instruct_answers.csv`
- `eval/v2026_06_answer_compare_summary.csv`
- `eval/v2026_06_answer_compare_detail.csv`
- `eval/v2026_06_retrieval_compare_summary.csv`
- `eval/v2026_06_retrieval_compare_detail.csv`

### 3. BGE Reranker Experiment

Reranker config:

- Retriever: `hybrid`
- Reranker: `BAAI/bge-reranker-v2-m3`
- Candidate count: 30
- Final top-k: 8

Result:

- Retrieval top-1 evidence hit improved to 19/20.
- Generation factual proxy stayed at 15/20.
- Average latency increased to 20.868s.

Interpretation:

- Useful as retrieval-quality reference.
- Not a good default generation path because latency rose without factual proxy gain.

### 4. Structured Patch-Change Records

New file:

- `data/snapshots/2026-06-official-updates/structured/change_records.json`

Records added:

- `DNF-2927756-CHANGE-01`
  - Character: 브레이커
  - Option: 질풍
  - Target skill: 타이드 바운드
  - Field: 기본 쿨타임
  - Before: 12초
  - After: 9초
  - Unchanged: 공격력 11.5% 감소

- `DNF-2927756-CHANGE-02`
  - Character: 브레이커
  - Option: 격랑
  - Target skill: 훅 샷
  - Field: 공격력 감소 수치
  - Before: 15.8% 감소
  - After: 17.6% 감소

Implementation notes:

- `scripts/run_rag_local_llm_eval.py` now loads snapshot-specific `structured/change_records.json` when `--use-structured-data` is set.
- The matching logic is intentionally conservative.
- A change record is used only when the question matches option name, before/after percent-second values, or target skill plus field.
- This avoids polluting generic skill questions. Example: Q011 asks normal 타이드 바운드 cooldown and should not inherit the 질풍 option-specific 12초 -> 9초 record.

## Latest Answer Comparison Summary

Current summary from `eval/v2026_06_answer_compare_summary.csv`:

| Run | Factual proxy | Format proxy | Refusal | Avg latency |
|---|---:|---:|---:|---:|
| BM25 + instruct | 13/20 | 20/20 | 3 | 6.061s |
| BGE-M3 + instruct | 13/20 | 20/20 | 3 | 4.219s |
| Hybrid + instruct | 15/20 | 20/20 | 2 | 4.613s |
| Hybrid + BGE reranker + instruct | 15/20 | 20/20 | 0 | 20.868s |
| Hybrid + structured change records + instruct | 16/20 | 20/20 | 0 | 4.273s |

Current best automatic proxy setting:

```text
Hybrid + structured change records + qwen3:4b-instruct-2507-q4_K_M
```

## Important Per-Question Notes

### Q011

Question:

```text
6/18 업데이트에서 브레이커 타이드 바운드의 쿨타임은 어떻게 변경되는가?
```

Expected:

```text
20초에서 18초로 감소
```

Latest structured answer:

```text
6/18 업데이트에서 브레이커 타이드 바운드의 쿨타임은 20초에서 18초로 감소합니다.
```

Note:

- Earlier structured matching was too broad and risked injecting the 질풍 option-specific 12초 -> 9초 record.
- Matching was tightened, and Q011 now answers correctly.

### Q012

Question:

```text
6/18 업데이트에서 브레이커 질풍 개화 옵션의 타이드 바운드 기본 쿨타임은 어떻게 바뀌는가?
```

Expected:

```text
질풍 개화 옵션에서 타이드 바운드 기본 쿨타임은 12초에서 9초로 바뀐다. 공격력 11.5% 감소 조건은 유지된다.
```

Latest structured answer:

```text
6/18 업데이트에서 브레이커의 '질풍' 스킬 개화 옵션의 타이드 바운드 기본 쿨타임은 12초에서 9초로 변경됩니다.
```

Status:

- Factual proxy pass.
- Structured record fixed this question.

### Q013

Question:

```text
6/18 공지에서 '공격력 15.8% 감소'가 '17.6% 감소'로 바뀐 브레이커 개화 옵션과 대상 스킬은 무엇인가?
```

Expected:

```text
브레이커의 '격랑' 개화 옵션에서 대상 스킬은 훅 샷이며, 공격력 감소 수치가 15.8%에서 17.6%로 바뀐다.
```

Latest structured answer:

```text
'격랑' 스킬 개화 옵션에서 훅 샷 스킬의 공격력 감소 수치가 15.8%에서 17.6%로 변경됨.
```

Status:

- Token/phrase factual proxy still marks it as fail.
- Human reading suggests it is essentially correct.
- Good candidate for manual rubric or LLM-as-judge review.

### Remaining Structured Failures

Under `hybrid_structured_instruct`, remaining proxy failures are:

- Q003
- Q013
- Q014
- Q018

These look like likely false negatives or partial-answer cases:

- Q003 answer says required material is deleted and EXP cost remains same, but may omit explicit `프라임 스텔라 10개`.
- Q013 answer appears correct to a human but fails token/phrase proxy.
- Q014 answer says `'모두 받기' 버튼이 추가됩니다`, which is concise but likely correct.
- Q018 answer says `48로 수정됩니다`, which is concise but likely correct.

## Commands Used

Hybrid structured generation:

```powershell
python scripts\run_rag_local_llm_eval.py `
  --questions questions\benchmark_questions_v2026_06.csv `
  --question-set-id benchmark_questions_v2026_06 `
  --doc-dir data\snapshots\2026-06-official-updates\processed_md `
  --metadata data\snapshots\2026-06-official-updates\metadata.csv `
  --retriever hybrid `
  --use-structured-data `
  --model qwen3:4b-instruct-2507-q4_K_M `
  --disable-thinking `
  --num-predict 512 `
  --num-ctx 8192 `
  --output eval\rag_v2026_06_hybrid_structured_instruct_answers.csv
```

Answer scoring:

```powershell
python scripts\score_answer_runs.py `
  --run bm25_instruct=eval\rag_v2026_06_bm25_instruct_answers.csv `
  --run bge_m3_instruct=eval\rag_v2026_06_bge_m3_instruct_answers.csv `
  --run hybrid_instruct=eval\rag_v2026_06_hybrid_instruct_answers.csv `
  --run hybrid_rerank_instruct=eval\rag_v2026_06_hybrid_rerank_instruct_answers.csv `
  --run hybrid_structured_instruct=eval\rag_v2026_06_hybrid_structured_instruct_answers.csv `
  --output eval\v2026_06_answer_compare_summary.csv `
  --detail-output eval\v2026_06_answer_compare_detail.csv
```

Verification:

```powershell
python scripts\smoke_check.py
git diff --check
python -m json.tool data\snapshots\2026-06-official-updates\structured\change_records.json
```

Verification results:

- Smoke check passed.
- JSON parsed successfully.
- `git diff --check` had only Windows LF/CRLF warnings, no whitespace errors.

## Questions For Claude

Please review the following:

1. Is `hybrid + structured change records` a reasonable next default for this staged 2026-06 RAG evaluation?
2. Does the conservative structured-record matching rule look safe enough, or should it be stricter?
3. For Q003/Q013/Q014/Q018, should these be treated as false negatives in the token/phrase factual proxy?
4. What would be a practical rubric or LLM-as-judge design for short Korean game-patch QA answers?
5. Should the project keep investing in reranking, or shift effort toward structured extraction and answer judging?
6. Would you recommend adding answer templates for patch-change questions, or would that overfit the benchmark?

## Current Recommendation From Codex

Codex's current recommendation:

- Use `hybrid + structured change records` as the current best speed/accuracy baseline.
- Keep reranker results as a retrieval-quality reference, not default generation path.
- Add manual or LLM-as-judge scoring for close-answer cases before claiming further model/RAG improvement.
- Continue structured extraction for patch-note tables where before/after relationships are easy to lose in plain Markdown chunks.
