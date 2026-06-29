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

## 초기 검색 검증

BM25 dry-run으로 모델 호출 전 검색 가능성을 확인했다.

| 설정 | 문항 수 | no context | top doc match |
|---|---:|---:|---:|
| doc-filtered BM25 | 20 | 0 | 20 / 20 |
| full-corpus BM25 | 20 | 0 | 20 / 20 |

Q013은 초안에서 6/11 공지와 6/18 공지의 브레이커 `격랑` 변경이 혼동되어 full-corpus top 문서가 어긋났다. 질문에 `15.8%`와 `17.6%` 수치를 포함하도록 수정한 뒤 full-corpus 기준 top doc match가 20/20으로 맞춰졌다.
