# 2026-06 benchmark question set design

## 목적

`questions/benchmark_questions_v2026_06.csv`는 `data/snapshots/2026-06-official-updates/`에 staging한 공식 업데이트 문서 8개를 대상으로 만든 draft 질문셋이다. 기존 `DOC-*` 기반 historical benchmark를 덮어쓰지 않고, 신규 `DNF-*` corpus에서 검색과 답변 생성이 정상적으로 되는지 확인하기 위한 평가셋이다.

## 기준 corpus

- corpus id: `dnf-official-updates-2026-06-staged`
- snapshot: `data/snapshots/2026-06-official-updates/corpus_snapshot.json`
- question set id: `benchmark_questions_v2026_06`
- question file: `questions/benchmark_questions_v2026_06.csv`
- doc id style: `DNF-<source_post_id>`

## 설계 원칙

- 최신 2026-06 공지 중심으로 구성했다.
- 가격, 구매 제한, 쿨타임, 레벨, 날짜처럼 오류 영향이 큰 수치를 포함했다.
- 단순 fact뿐 아니라 변경 전후 비교, 조건 판단, 접근 경로, 요약형 질문을 섞었다.
- 대규모 업데이트 랜딩 문서 `DNF-2927617`은 수집 본문에 네비게이션 텍스트가 섞여 있어, 문서에 명확히 남은 업데이트 날짜와 구성요소 확인 질문으로만 제한했다.
- active `benchmark_questions.csv`와 결과 수치를 섞지 않기 위해 별도 question set id를 사용한다.

## 문항 분포

| doc_id | 문서 | 문항 수 | 주요 평가 포인트 |
|---|---|---:|---|
| `DNF-2927810` | 6/25 정기점검 | 5 | 상점 가격/제한, 재료 삭제, 매칭 제재, 패턴 시간 |
| `DNF-2927822` | 6/25 던파ON | 5 | 버전, 다운로드 시간, 무기고 조회 조건/경로, 제거 서비스 |
| `DNF-2927756` | 6/18 정기점검 | 3 | 브레이커 타이드 바운드/질풍/격랑 변경 |
| `DNF-2927691` | 6/11 정기점검 | 6 | 아라드 나침반, 몬스터명, 브레이커 스킬 변경, 장비 수치 |
| `DNF-2927617` | 시즌 11 Act 2 랜딩 | 1 | 업데이트 날짜와 구성요소 |

## 실행 예시

```powershell
python scripts\run_rag_local_llm_eval.py `
  --questions questions\benchmark_questions_v2026_06.csv `
  --question-set-id benchmark_questions_v2026_06 `
  --doc-dir data\snapshots\2026-06-official-updates\processed_md `
  --metadata data\snapshots\2026-06-official-updates\metadata.csv `
  --retriever bm25 `
  --dry-run
```

이 실행은 모델을 호출하지 않고 검색 결과만 확인한다. 실제 답변 평가를 실행할 때는 `--dry-run`을 제거하고, 모델/검색기/서비스 톤 설정을 run manifest와 함께 기록한다.

```powershell
python scripts\run_rag_local_llm_eval.py `
  --questions questions\benchmark_questions_v2026_06.csv `
  --question-set-id benchmark_questions_v2026_06 `
  --doc-dir data\snapshots\2026-06-official-updates\processed_md `
  --metadata data\snapshots\2026-06-official-updates\metadata.csv `
  --retriever bm25 `
  --model qwen3:4b-instruct-2507-q4_K_M `
  --disable-thinking `
  --num-predict 512 `
  --num-ctx 8192 `
  --output eval\rag_v2026_06_bm25_instruct_answers.csv
```

`top_k=8` 기본 RAG context는 일부 문항에서 Ollama 기본 context window인 4096 tokens를 넘을 수 있다. `--num-ctx 8192`는 이 실행을 안정적으로 재현하기 위한 설정이다.

## 초기 검색 검증

BM25 dry-run으로 모델 호출 전 검색 가능성을 확인했다.

| 설정 | 문항 수 | no context | top doc match |
|---|---:|---:|---:|
| doc-filtered BM25 | 20 | 0 | 20 / 20 |
| full-corpus BM25 | 20 | 0 | 20 / 20 |

Q013은 초안에서 6/11 공지와 6/18 공지의 브레이커 `격랑` 변경이 혼동되어 full-corpus top 문서가 어긋났다. 질문에 `15.8%`와 `17.6%` 수치를 포함하도록 수정한 뒤 full-corpus 기준 top doc match가 20/20으로 맞춰졌다.

## BM25/BGE-M3/hybrid + Qwen3 instruct 실행 결과

2026-06-30에 Ollama `qwen3:4b-instruct-2507-q4_K_M` 모델로 BM25, BGE-M3, hybrid RAG 답변 생성을 실행했다. 이 결과는 기존 active `benchmark_questions_v2026_05` 결과를 대체하지 않는 staged corpus 검증용 결과다.

생성 결과:

| 설정 | 문항 수 | status success | factual proxy | format proxy | meta reasoning | refusal | 평균 지연 |
|---|---:|---:|---:|---:|---:|---:|---:|
| BM25 + `qwen3:4b-instruct-2507-q4_K_M` | 20 | 20 / 20 | 13 / 20 | 20 / 20 | 0 | 3 | 6.061s |
| BGE-M3 + `qwen3:4b-instruct-2507-q4_K_M` | 20 | 20 / 20 | 13 / 20 | 20 / 20 | 0 | 3 | 4.219s |
| Hybrid + `qwen3:4b-instruct-2507-q4_K_M` | 20 | 20 / 20 | 15 / 20 | 20 / 20 | 0 | 2 | 4.613s |

검색 proxy:

| 설정 | 문항 수 | evidence hit | top-1 evidence hit | avg token recall | avg top-1 token recall |
|---|---:|---:|---:|---:|---:|
| full-corpus BM25 dry-run | 20 | 19 / 20 | 18 / 20 | 0.974 | 0.935 |
| full-corpus BGE-M3 dry-run | 20 | 20 / 20 | 18 / 20 | 0.997 | 0.931 |
| full-corpus hybrid dry-run | 20 | 20 / 20 | 18 / 20 | 1.000 | 0.924 |

생성 CSV와 manifest:

- `eval/rag_v2026_06_bm25_instruct_answers.csv`
- `eval/rag_v2026_06_bm25_instruct_answers.manifest.json`
- `eval/rag_v2026_06_bge_m3_instruct_answers.csv`
- `eval/rag_v2026_06_bge_m3_instruct_answers.manifest.json`
- `eval/rag_v2026_06_hybrid_instruct_answers.csv`
- `eval/rag_v2026_06_hybrid_instruct_answers.manifest.json`
- `eval/v2026_06_answer_compare_summary.csv`
- `eval/v2026_06_answer_compare_detail.csv`
- `eval/v2026_06_retrieval_compare_summary.csv`
- `eval/v2026_06_retrieval_compare_detail.csv`

Raw dry-run output인 `eval/v2026_06_*_full_dry_run.csv`와 manifest는 `eval/*dry_run*` ignore 규칙에 따라 로컬 중간 산출물로 둔다. 추적 대상 검색 결과는 `v2026_06_retrieval_compare_*` 요약/상세 CSV다. BGE-M3 embedding cache 역시 `data/cache/` ignore 규칙에 따라 추적하지 않는다.

해석:

- 검색 단계는 BM25도 안정적이었지만, BGE-M3와 hybrid가 evidence hit 20/20으로 더 높았다.
- BGE-M3 단독은 검색 hit과 평균 지연은 개선했지만 factual proxy는 BM25와 같은 13/20이었다.
- Hybrid는 factual proxy를 15/20으로 올렸고 refusal도 3건에서 2건으로 줄였다. 현재 2026-06 staged corpus의 가장 나은 자동 proxy 설정은 hybrid다.
- Q001, Q015는 BM25 대비 hybrid에서 개선됐다. Q017은 BGE-M3 단독에서는 실패했지만 hybrid에서는 BM25와 같이 통과했다.
- 남은 hybrid 실패 중 Q003, Q014, Q018은 답변이 부분적으로 맞지만 token/phrase 기반 proxy가 보수적으로 실패 처리한 false negative 가능성이 있다.
- Q012와 Q013은 검색 context를 받은 뒤에도 모델이 보수적으로 거절한 실제 개선 대상이다. 다음 단계는 해당 문항의 retrieved context를 수동 검토하고, chunk window/top-k 또는 answer prompt를 조정해 근거 활용률을 높이는 것이다.
