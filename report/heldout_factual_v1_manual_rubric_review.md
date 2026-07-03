# Factual Held-out v1 — 수동 rubric 채점

작성일: 2026-07-04
대상: `report/heldout_factual_ablation_v1.md`의 held-out 25문항, 답변 CSV `eval/ablation_v2026_06_heldout_full_completeness_answers.csv`(구조화 record on/off 5개 조건이 전부 23/25로 동률이었으므로 대표로 1개 조건만 채점)
루브릭: `eval/evaluation_rubric.md`
채점 결과: `eval/heldout_factual_v1_manual_rubric.csv`

## 왜 필요한가

`heldout_factual_ablation_v1.md`의 23/25는 token/phrase recall 기반 자동 factual proxy 결과다. README와 오류 분석 요약에도 이미 "Q016은 사실상 정답인데 자동 proxy가 fail로 잡은 사례가 있다"는 known false negative가 기록돼 있다. held-out에는 아직 수동 채점이 없었으므로, 25문항 전부를 사람이 다시 읽고 critical gate와 완전성을 확인했다.

## 결과 요약

| 자동 proxy | 수동 rubric |
|---|---|
| 23/25 pass, 2/25 fail (HF023, HF024) | 22/25 완전 pass, **1/25 completeness 경고(HF004)**, 2/25 진짜 fail(HF023, HF024) |

- **HF023, HF024는 자동 proxy와 수동 채점이 일치한다.** 둘 다 gold가 요구하는 조건절(HF023: 중간보스 생략 게이트 개방 사실, HF024: 1개 게이트가 추가됐다는 변경 근거)을 답변이 누락했다. 자동 proxy fail은 정확했다.
  - **critical gate 라벨 보정**: 처음에는 이 둘을 `numeric_error_gate=FAIL`로 표시했는데, 이건 부정확했다. 루브릭의 "중대 수치 오류" gate는 핵심 수치가 **틀렸을 때** FAIL이지, 조건절/변경 근거가 **누락**됐을 때 쓰는 gate가 아니다. HF023/HF024 둘 다 언급한 수치(HF024는 최종 총 3개) 자체는 틀리지 않았다. 그래서 두 문항 다 `numeric_error_gate`는 PASS로 정정하고, 실패는 completeness 점수(HF023 0점, HF024 1점)로만 반영했다. verdict(전체 판정)는 여전히 `fail`로 동일하다 — 어느 항목으로 감점할지만 바로잡았다.
- **HF004는 자동 proxy가 놓친 completeness 문제다.** gold는 "캐릭터별 필터"와 "무기 타입/레어리티 필터" 두 가지를 모두 요구하는데, 모델 답변은 무기 타입/레어리티 필터만 말하고 캐릭터별 필터를 완전히 빠뜨렸다. token recall 기준으로는 핵심 키워드(무기 타입, 레어리티)가 들어있어 pass 처리됐지만, 완전성 기준으로는 2점(3점 만점)이 맞다. Critical gate FAIL은 아니다(수치 오류나 환각이 아니라 단순 누락이므로).
- **HF025는 확인이 필요해서 원문까지 대조했다.** 모델이 "신실한 소코르스"라는, evidence 문장에는 없는 단어를 답변에 포함해서 처음엔 환각 의심 항목으로 표시했다. 원본 문서(`data/processed_md/DOC-02_...md`) 372행을 확인한 결과 "신실한 소코르스"가 몬스터의 정식 명칭이었다. 즉 모델이 검색된 다른 chunk에서 정확한 전체 명칭을 가져온 것이고 환각이 아니다. 자동 proxy의 pass 판정은 맞았다.
- 25문항 전부 critical gate 4종(환각/과잉추론, 중대 수치 오류, 라이브 서버 기준 오인, 범위 통제)은 PASS였다. HF023/HF024/HF004의 실패는 critical gate가 아니라 completeness 점수 하락으로 나타난다 — 이 held-out set에서 관찰된 실패 유형은 "환각"이나 "수치 오류"가 아니라 전부 "조건절/필터 조건 누락"류의 completeness 문제였다는 뜻이다.

## 결론

- 이번 수동 채점은 held-out 23/25라는 자동 수치를 뒤집지 않는다. 두 개의 실제 fail(HF023/24)은 자동 proxy와 수동 판단이 일치했다.
- 다만 자동 proxy에는 없는 새로운 관찰이 하나 나왔다: **HF004는 부분적으로 불완전한 답변인데 자동 proxy는 이를 잡아내지 못한다.** 표에 여러 필터 조건이 나열될 때 그중 일부만 답하면 token recall은 통과하지만 실제 완전성은 떨어진다는, 이 프로젝트가 이미 Q002(인접 상품 정보 혼입)에서 지적한 것과 같은 계열의 실패 패턴이다.
- HF025는 겉보기 환각 후보였지만 원문 대조로 무혐의 처리했다 — 자동 proxy를 의심 없이 신뢰하지 않고 원문까지 확인하는 수동 검증의 가치를 보여주는 사례로 남긴다.

## 산출물

- `eval/heldout_factual_v1_manual_rubric.csv`
