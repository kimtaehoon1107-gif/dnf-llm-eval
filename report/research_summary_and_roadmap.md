# DNF LLM 평가 프로젝트: 연구 요약과 로드맵

작성일: 2026-07-01 (최종 갱신: 2026-07-04, factual/safety held-out 및 제출 문서 갱신 반영)
브랜치: `codex/v2026-06-results` (로컬 전용, origin/main보다 앞섬, 아직 push 안 됨)
용도: 연구 과정, 현재 상태 총정리, 현재 목표, 앞으로 진행 방향을 한 문서로 정리. 상세 색인은 `report/research_overview_master.md` 참고.

핵심 한 줄: 이 프로젝트는 "높은 점수를 만든 프로젝트"가 아니라 "높은 점수가 믿을 만한지 스스로 검증하는 평가 프로토콜을 만든 프로젝트"다.

---

## 1. 연구 과정 (시간순)

| 단계 | 한 일 | 핵심 결과 | 신뢰도 |
|---|---|---|---|
| ① 수집·벤치마크 설계 | 던파 공식 문서 수집 → Markdown corpus, 벤치마크 22문항, 안정 ID·snapshot·manifest | 재현 가능한 평가 기반 | 높음 |
| ② Baseline vs RAG | RAG 없이 vs 있이 문서 질문 정확도 비교 | 문서 질문 11.27 → 18.86 / 21 | 높음 |
| ③ Retriever 비교 | BM25 heuristic vs BGE-M3 | Top-1 hit 19/22 vs 21/22 → BGE-M3 채택 | 높음 |
| ④ 생성 ablation | `qwen3:4b` → instruct, +service tone, +structured | format 9/22 → 22/22, 메타발화 13 → 0 | 높음 |
| ⑤ Safety gate (키워드) | 인젝션·유출·악용·현금화·OOD 차단 규칙 | 명시적 10/10, stealth 0/10 (한계 기록) | 중간 |
| ⑥ 2026-06 재평가 | 최신 문서 staging, 20문항 신규 세트로 재실험 | hybrid+structured 16/20, reranker 제외(latency 4.5배) | 높음 |
| ⑦ 6/30 확장 | 마무리 리뷰 + 편향셋 24 + 과차단셋 20, 정밀도 축 추가 | 편향 24/24 gate PASS, 과차단 1/20 | 중간 |
| ⑧ 7/1 심화 | structured fix, DeepEval 통합, intent gate e2e | factual 20/20, 공격 50/50·오탐 0 | 낮음 (dev/test-informed) |
| ⑨ 7/1 factual held-out v1 | source_relation/completeness 2x2 ablation을 dev·held-out에서 실행 | held-out 23/25 전 조건 동률, record 발동 0/25 | 검증됨 (구조화 이득 미확인) |
| ⑩ 7/2~7/3 safety held-out v1~v6 | blind held-out↔regression 반복, v6를 사전선언 최종 검증으로 종료 | attack block 12/24(50.0%), FP 0/24 | 검증됨 (절대 성능 낮음) |
| ⑪ 7/4 safety held-out 재검산 | v1~v6를 단순 합산하지 않고, 실제로 blind였던 조합만 재계산 + 현재 규칙을 과거 세트에 소급 적용 | 구식 공격 유지 75.0%(90/120) vs 유일한 진짜 신규 세트(v6) 50.0%(12/24), 라운드 간 recall 비단조(58→50→37.5→50%) | 검증됨 (v6만 진짜 blind, v5는 순환이라 제외) |
| ⑫ 7/4 real_world_harm 카테고리 재진단 | v6의 0/4 카테고리 원문 4개를 직접 읽고 원인 분석 | "규칙이 약함"이 아니라 "v6에서 처음 도입된 taxonomy라 대응 rule 자체가 없었음"으로 원인 정정. 지금 패치 안 하고 v7 스코프로 이관 | 진단 완료, 수정은 의도적으로 보류 |
| ⑬ 7/4 DeepEval fail 6건 독립 재검증 | 원 판정을 안 보고 문항·근거·답변·judge reason 재대조 | 5/6 확정(4건은 reason과 score 자체가 내적 모순), 1/6(Q003)은 경계 사례로 남김 | 검증됨 |
| ⑭ 7/4 factual held-out v1 수동 rubric | 25문항 전체를 자동 proxy 대신 사람이 다시 채점 | HF023/24 fail 확정, HF004는 자동 proxy가 놓친 completeness 누락 신규 발견, HF025는 원문 대조로 환각 의심 해소 | 검증됨 |
| ⑮ 7/4 semantic safety classifier 프로토타입 | BGE-M3 임베딩 1-NN, 프로토타입은 dev 세트만 사용 | v6에서 83.3%(20/24) vs 규칙 50.0%(12/24), real_world_harm 0/4→3/4 | retrospective prototype (아이디어 선택이 v6 결과를 본 뒤 이뤄졌을 수 있어 완전한 blind 아님), 정식 headline은 v7 사전등록 이후 |
| ⑯ 7/4 자동 change-record 추출기 프로토타입 | 화살표/서술형/표 3패턴 정규식 추출기를 2026-06 staged corpus에 적용 | hand-authored 5건 중 2건 완전복원+1건 부분+2건 실패, 35개 후보 추가 발견(가격 변경 건은 shop_items.json에 이미 있어 "신규 발견" 주장 정정, 몬스터 개명 등은 진짜 신규) | 프로토타입, 표 패턴 재설계 + 스키마 분류 단계 필요 |

각 단계의 핵심 설계는 모델 호출이 아니라 평가 장치(벤치마크 질문, 지표, critical gate, 실패 분석 기준)다. 게임 데이터를 썼지만 방법론은 도메인 무관하게 금융 등 다른 QA에도 적용된다.

---

## 2. 총정리 (현재 성적표)

| 축 | 지표 | 현재 값 | 신뢰도 |
|---|---|---|---|
| 검색 | Top-1 evidence hit | BGE-M3 21/22 | 높음 |
| 생성 형식 | Format proxy | 22/22 (05), 20/20 (06) | 높음 |
| 생성 사실성 | Factual proxy (06, dev) | structured fix 후 20/20 | 낮음 (dev/test-informed) |
| 생성 사실성 | Factual proxy (held-out v1, 25문항) | 23/25, 구조화 on/off 전 조건 동률 (record 발동 0/25) | 검증됨 (구조화 이득 미확인) |
| 안전 재현율 | 공격 차단 (dev, intent gate) | 50/50 | 낮음 (dev/test-informed) |
| 안전 재현율 | 공격 차단 (held-out v6, intent_rules_v5) | 12/24 (50.0%) | 검증됨 (절대 성능은 낮음) |
| 안전 정밀도 | 정상 질문 과차단 | 키워드 1/20, intent 0/20 (dev), held-out v6 0/24 | 중간~검증됨 |
| 편향 | critical gate PASS | 24/24 | 중간 (dev, held-out 아님) |
| 지연 | 평균 latency | 약 4.4s | 높음 |

신뢰도 "낮음(dev/test-informed)"은 자기 평가셋에 맞춰져 있어 일반화를 장담할 수 없다는 뜻이고, "검증됨"은 fresh blind held-out으로 실측했다는 뜻이다. 검증됐다고 성능이 좋다는 뜻은 아니다.

### 핵심 이슈: test-informed 오염 (7/3, held-out으로 검증 완료)

- structured fix 20/20은 사실상 정답 주입에 가깝다는 우려 → **factual held-out v1로 확인.** held-out 25문항에서는 structured record가 0/25 발동해 구조화 on/off가 no-op이었고, 전 조건 23/25로 동률이었다. `report/heldout_factual_ablation_v1.md`.
- intent gate 50/50·오탐 0도 규칙을 평가셋 문장에서 역산했다는 우려 → **safety held-out v1~v6로 확인.** 최종 v6에서 12/24(50.0%)로 나왔고, real-world harm(0/4)·malware/prompt-injection(1/4)은 특히 취약했다. `report/safety_eval_final_report_v6.md`.
- 편향 24/24도 record 주입은 아니지만 in-distribution 개발셋이다. held-out 검증은 아직 안 함.

이 오염을 스스로 드러내고 held-out으로 재측정한 것이 평가 직무 관점에서는 오히려 최대 강점이다. 자기 평가의 함정을 발견하는 능력이 이 직무의 본질이기 때문이다.

### 라벨링 상태

- 완료: `README.md`, `index.html`, `report/final_closing_review.md`, `report/final_portfolio_report.md`, `report/application_summary.md`에 dev/test-informed caveat와 held-out 실측값을 함께 반영했다(7/4).
- 완료: factual은 dev 20/20과 held-out 23/25(record 0/25 발동)를 분리했고, safety는 dev/regression 50/50과 fresh v6 12/24, FP 0/24를 분리했다. Semantic classifier 20/24는 retrospective prototype으로만 표기한다.

---

## 3. 현재 목표

1. 제출용: 카카오뱅크 'AI 서비스 품질 및 안전성 평가' 지원(마감 2026-07-13, 과제전형 7/21~25)에 쓸 실험 결과와 보고서 완성.
2. 내용 완성도: 최신 수치의 test-informed 오염을 held-out 검증으로 정량화하고, "dev vs held-out"을 나란히 보고하는 구조로 전환.
3. 서술: 완벽한 점수가 아니라 검색 품질·생성 사실성·서비스 형식·안전 recall/precision·편향·자동 judge 한계를 각각 분리 측정하고 실패를 분석하는 흐름을 보여준다.

---

## 4. 앞으로 진행할 것 — Agent Execution Instructions

**(7/4 상태) 아래 0~4, 6은 실행 완료됐다. 5(judge validation)는 future work로 보류한다. 원문은 실행 기록 겸 다음 라운드(judge validation, factual v2, extractor, safety v7) 재사용을 위해 그대로 남긴다.**

이 블록은 "결과가 나온 뒤 변명하지 못하게" 하는 감사 프로토콜이다. 실행자(Codex/Claude)에게 그대로 전달한다.

목표: 최신 dev 결과(factual 20/20, safety 50/50, bias 24/24)의 일반화 성능을 held-out으로 검증한다. held-out 결과에 맞춰 record/규칙/프롬프트/threshold/judge를 수정하지 않는다.

**0. 선행 라벨링 (push 전 필수) — 완료**
`README.md`, `index.html`, `report/final_closing_review.md`, `report/final_portfolio_report.md`, `report/application_summary.md`의 20/20·50/50·24/24에 caveat를 단다. 초기 caveat는 일반 보류 문구였고, 7/4에는 실제 held-out 수치로 갱신했다.

> 주의: 2026-07-01 structured fix 및 intent safety gate 결과는 dev/test-informed 결과다. 동일 문항의 실패 분석을 바탕으로 record와 rule을 보강한 뒤 재측정했으므로 held-out 일반화 성능으로 해석하지 않는다. Factual held-out에서는 모든 조건이 23/25였고 structured record는 0/25 발동했다. Safety 최종 fresh v6는 12/24, FP 0/24다. Semantic classifier 20/24는 retrospective prototype으로 둔다.

**1. Pre-register before running held-out — 완료 (factual v1, safety v1~v6 각각 사전등록)**
- held-out 실행 전 비교 조건, 해석 기준, headline 수치 선택 규칙을 문서에 먼저 기록한다.
- 예: "held-out에서 full structured가 atomic-only보다 명확히 낫지 않으면 headline 수치는 atomic-only 기준으로 보고한다."
- 결과를 본 뒤 threshold, record, safety rule, judge prompt를 수정하지 않는다.

**2. Freeze protocol — 완료**
- held-out question/gold/evidence QA를 먼저 완료한다. gold는 evidence(원문 문장)와 교차검증해 실제 원문과 일치하는지 확인한다(blind 제작과 별개 축).
- QA 완료 후 파일 hash와 manifest를 생성한다.
- held-out set은 규칙 수정 전에 별도 커밋으로 먼저 고정한다. 커밋 순서가 "제작이 규칙보다 먼저"라는 감사 추적이 된다.
- 이후 모델 설정과 ablation만 실행한다.
- 크기 원칙: dev는 small-n 겸손하게 읽되, held-out은 하락 검출이 목적이므로 검정력을 위해 키운다. factual held-out은 가능하면 25문항 이상.
- blind 제작: 문항을 만들 때 `change_records.json`과 `scripts/safety_intent.py`를 열지 않는다. 원문 패치노트/시나리오만 본다.

**3. Factual ablation matrix — 완료 (`report/heldout_factual_ablation_v1.md`, held-out 23/25 동률, record 발동 0/25)**
- `source_relation on/off × completeness rule on/off` 2×2 factorial + no-structured baseline로 실행한다.
- completeness rule은 `run_rag_local_llm_eval.py`의 must_include/answer_requirement 블록(약 1062행)과 시스템 프롬프트 규칙(약 1171행)을 토글해 구현한다.
- dev 20문항과 held-out 양쪽에서 각 셀 factual proxy를 `eval/ablation_source_relation_summary.csv`에 기록한다.
- small-n에서는 1~2문항 차이를 우열로 단정하지 않는다(동률권). 3문항 이상 또는 동일 오류 유형 반복 시 의미 있는 차이로 본다.
- 처방: ablation이 "손으로 쓴 source_relation이 일한다"를 보이면, 다음 방향은 원문에서 atomic 필드를 자동 추출하는 extractor다.

**4. Safety held-out comparison — 완료 (`report/safety_eval_final_report_v6.md`, attack 12/24, benign FP 0/24)**
- keyword gate와 intent gate를 같은 held-out safety set에서 모두 실행한다.
- attack recall, benign false positive rate를 함께 보고한다.
- intent gate 단독 수치만 headline으로 쓰지 않는다.

**5. Judge validation — 미착수**
- custom JSON judge는 held-out 일부에서 human verdict와 일치율을 먼저 측정한다.
- judge agreement를 별도 지표로 보고한다.
- judge 결과는 최종 판정자가 아니라 triage signal로 사용한다.

**6. Reporting rule — 완료 (README/final_*/Pages에 dev/regression, held-out, retrospective prototype을 분리 반영)**
- dev/test-informed 결과와 held-out 결과를 같은 표에 나란히 둔다.
- held-out에서 점수가 떨어지면 실패가 아니라 과적합을 검출한 평가 성과로 해석한다.

**금지 사항**: held-out을 본 뒤 record·intent 규칙·프롬프트·judge를 수정해 재측정하는 것. 이는 오염이며 held-out의 의미를 무효화한다. `git add -A` 금지(repo에 CRLF 노이즈 다수, 지정 파일만 커밋).

---

## 5. 마감(2026-07-13) 대비 스코프

(7/4 갱신) "제출 필수" 항목은 모두 끝났고, 애초에 "문서화로 대체"하려 했던 safety held-out도 실제로 v1~v6까지 실행 완료됐다. README/final_*/Pages의 headline도 held-out 실측값 중심으로 갱신했다. 남은 스코프는 백업과 공개 반영이다.

- 완료: 라벨링, factual held-out 1개(v1) 제작·freeze·2×2 ablation, safety held-out v1~v6 전체 사이클, held-out 실측값 문서 반영, review brief 작성.
- 남음(7/13 전): 지정 파일만 커밋하고 push해 GitHub/Pages를 최신화한다.
- future work: judge validation, semantic safety v7 사전등록, atomic record extractor 정식 검증. 이번 제출 마무리에서는 새 모델/규칙 튜닝을 하지 않는다.

---

## 6. 지금 상태와 다음 액션

- 라벨링: README/final_*/Pages 포함 전부 완료 확인(7/4).
- factual held-out: v1 완료(`report/heldout_factual_ablation_v1.md`). 구조화 record가 held-out에서 0/25 발동 — 다음은 v2 반복이 아니라 atomic record 자동 extractor.
- safety held-out: v1~v6 완료, v6를 최종 결과로 라운드 종료(`report/safety_eval_final_report_v6.md`).
- push: 아직 대기(로컬 커밋 백업 안 됨). public 포트폴리오(main/Pages)는 push 전까지 안 바뀜.

다음 액션 순서: (1) 지정 파일만 커밋 → (2) 브랜치 push로 백업 및 GitHub Pages 최신화 → (3) 제출 전 링크/README 최종 확인. custom judge validation, semantic safety v7, atomic record extractor 정식화는 future work로 보류.
