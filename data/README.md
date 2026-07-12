# data/ 구조 안내

이 폴더에는 던파 공식 업데이트 문서 corpus가 **두 군데**로 나뉘어 있습니다. 중복처럼 보이지만 의도적인 분리이고, 합치면 벤치마크 재현성이 깨집니다. 이 문서는 왜 나뉘어 있는지와 문서 간 매핑을 기록합니다.

## 왜 두 corpus로 나뉘어 있나

- `data/processed_md/` (5개 문서, `DOC-01`~`DOC-05`): 기존 활성 벤치마크(`questions/benchmark_questions.csv`, 22문항)가 참조하는 corpus. 이 문서들의 특정 시점 내용에 맞춰 gold answer/evidence가 이미 검증돼 있습니다.
- `data/snapshots/2026-06-official-updates/processed_md/` (8개 문서, `DNF-*`): 2026-06 재수집분. `questions/benchmark_questions_v2026_06.csv` 등 2026-06 질문셋이 참조합니다.

**둘을 합치거나 어느 한쪽으로 덮어쓰면 안 됩니다.** 공식 공지 글은 게시 후에도 내용이 추가/수정될 수 있습니다. 예를 들어 `DOC-01`(2026-05-27 수집)과 `DNF-2927522`(2026-06-29 재수집)는 같은 게시글(`source_post_id=2927522`)이지만, 나중 버전에는 "게임 실행 런처 디자인 개선", "아바타명 오탈자 수정" 같은 내용이 추가돼 있습니다. `benchmark_questions.csv`의 정답/근거는 `DOC-01` 시점 내용으로 검증된 것이라, 이후 버전으로 덮어쓰면 그 검증이 무효화됩니다.

## 문서 매핑 (source_post_id 기준)

| source_post_id | 활성 corpus (`DOC-*`) | 2026-06 snapshot (`DNF-*`) | 비고 |
|---|---|---|---|
| 2927522 | `DOC-01` (2026.05.28 수집) | `DNF-2927522` (2026.05.27 수집, 재수집) | **내용 다름** — snapshot 쪽에 런처 개선/오탈자 수정 등 추가됨 |
| 2927399 | `DOC-02` | `DNF-2927399` | 같은 게시글, 재수집 시점 다름 |
| 2927392 | `DOC-03` | `DNF-2927392` | 같은 게시글, 재수집 시점 다름 |
| 2927335 | `DOC-04` | (snapshot에 없음) | 활성 corpus 전용 |
| 2927233 | `DOC-05` | (snapshot에 없음) | 활성 corpus 전용 |
| 2927617 | (활성 corpus에 없음) | `DNF-2927617` | snapshot 전용 |
| 2927691 | (활성 corpus에 없음) | `DNF-2927691` | snapshot 전용 |
| 2927756 | (활성 corpus에 없음) | `DNF-2927756` | snapshot 전용 |
| 2927810 | (활성 corpus에 없음) | `DNF-2927810` | snapshot 전용 |
| 2927822 | (활성 corpus에 없음) | `DNF-2927822` | snapshot 전용 |

겹치는 3개(2927522/2927399/2927392)도 **내용이 같다고 가정하지 말고** 필요하면 직접 diff로 확인하세요.

## 구조화 데이터도 같은 원칙으로 나뉨

- `data/structured/shop_items.json`: 활성 corpus(`DOC-*`)용 상점 구조화 데이터
- `data/snapshots/2026-06-official-updates/structured/shop_items.json`, `change_records.json`: 2026-06 snapshot(`DNF-*`)용. 두 `shop_items.json`은 이름은 같지만 **다른 파일이며 대상 문서가 다릅니다.**

## 앞으로 재수집할 때 (스냅샷 폴더가 계속 늘어나는 문제 방지)

`data/snapshots/`에 새 폴더(예: `2026-07-official-updates`)를 또 만들 때마다 폴더가 계속 쌓입니다. `report/`가 safety v1~v5 raw 산출물로 118개까지 부풀었다가 정리한 것과 같은 문제가 여기서도 반복될 수 있습니다. 권장 정책:

1. 새 snapshot을 만들 때는 기존 활성 corpus(`data/processed_md/`)를 덮어쓰지 않는다 (README.md에 이미 명시된 원칙).
2. 새 snapshot이 검증되고 그걸 쓰는 질문셋이 확정되면, 그 이전 snapshot 중 더 이상 어떤 질문셋도 참조하지 않는 것은 `data/archive/`로 옮긴다.
3. 이 문서(`data/README.md`)의 매핑 표를 그때마다 갱신한다.

## 참고

- `data/metadata.csv`, `data/snapshots/*/metadata.csv`: 각 corpus의 `doc_id`↔`source_post_id`↔`posted_date` 매핑 원본
- `data/corpus_snapshot.json`, `data/snapshots/*/corpus_snapshot.json`: 문서 목록과 해시 기록 (재현성 검증용)
- 최상위 `README.md`의 "프로젝트 구조" 절에 이 두 corpus의 사용 목적이 서술돼 있음
