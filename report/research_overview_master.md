# DNF LLM 평가 프로젝트: 전체 연구 총정리

작성일: 2026-07-01 (최종 갱신: 2026-07-04, factual/safety held-out v1~v6 및 제출 문서 갱신 반영)
대상 브랜치: `codex/v2026-06-results`
목적: 지금까지의 연구 과정을 처음부터 끝까지 하나로 정리하고, 현재 목표와 앞으로 진행할 방향을 명확히 한다. 흩어진 개별 보고서를 잇는 상위 색인 문서다.

---

## 0. 한 장 요약 (TL;DR)

던전앤파이터 공식 업데이트 문서를 근거로 로컬 LLM의 답변 품질과 안전성을 평가하는 파이프라인 프로젝트다. 챗봇 데모가 아니라 `문서 수집 → 벤치마크 설계 → RAG 검색 → 답변 생성 → 지표 설계 → 실패 분석`의 평가 과정 자체가 핵심이다.

지금까지 확인한 큰 결론은 세 가지다. 첫째, RAG는 비RAG 대비 문서 기반 질문 정확도를 크게 올렸다(11.27 → 18.86 / 21). 둘째, 검색은 BGE-M3, 생성은 qwen3 instruct variant로 갈 때 품질과 속도가 가장 안정적이었다. 셋째, 최근(7/1) structured fix와 intent safety gate는 dev/regression에서는 크게 개선됐지만, held-out 감사에서 각각 record 비전이와 fresh v6 12/24 한계가 확인됐다.

따라서 최종 포지션은 "높은 점수"가 아니라 "높은 점수의 출처와 신뢰 범위를 감사 가능하게 표시한 평가 포트폴리오"다. v7과 추가 모델/규칙 개선은 future work로 미루고, 현재 마무리는 README, final report, Pages, review brief에서 dev/regression·held-out·retrospective prototype을 분리해 전달하는 데 둔다.

---

## 1. 프로젝트 정체성과 목적

- 무엇인가: 게임 도메인(던파) 문서 기반 LLM 평가 파이프라인. Python 3.10+, Selenium 수집, BM25 heuristic / BGE-M3 검색, Ollama + Qwen3 4B, 규칙 기반 safety gate, 수동 rubric.
- 왜 하는가: 게임/금융권을 포함한 'AI 서비스 품질 및 안전성 평가' 직무의 핵심 업무를 작게 재현한다. 즉 도메인 LLM 벤치마크 구성, 평가 지표·기준 개발, 응답 품질 평가, 환각·편향 원인 분석과 개선 제안.
- 직무 연결: 사례 데이터는 게임이지만, 평가 방법론(벤치마크 설계, 지표, 실패 분석, 안전성 recall·precision, 편향, judge 설계)은 도메인 무관하게 금융 등 다른 QA에도 그대로 적용된다는 점이 어필 포인트다.

---

## 2. 평가 파이프라인 개요

최종 파이프라인은 다음 순서다.

```
질문 → Safety Gate → Retriever(BGE-M3/hybrid) → Context Builder(+구조화 근거) → Generator(qwen3 instruct) → Evaluator/Logger → Reports
```

설계한 핵심 자산은 모델 호출이 아니라 평가 장치다.

| 자산 | 의미 | 위치 |
|---|---|---|
| Benchmark questions | 유저가 물을 만한 문서 기반 질문 + 기준 정답 + 근거 문장 | `questions/benchmark_questions*.csv` |
| Structured data | 표형 정보(상점, 패치 변경표)를 JSON record로 별도 추출한 보조 근거 | `data/**/structured/*.json` |
| Safety gate | 인젝션·유출·악용·현금화·OOD 등을 답변 전에 차단하는 규칙 baseline | `questions/adversarial_*.csv`, `scripts/safety_intent.py` |
| Manual rubric | 6항목 점수 + 4개 binary critical gate | `eval/evaluation_rubric.md`, `eval/bias_safety_evaluation_rubric.md` |

---

## 3. 연구 흐름 (시간순 단계별)

### 3-1. 데이터 수집과 벤치마크 설계

던파 공식 업데이트 문서를 Selenium으로 수집해 Markdown corpus로 정리했다. 초기 corpus(2026-05, active)는 문서 5개 중심이며 벤치마크 질문 22개를 설계했다. 문서 ID는 초기 `DOC-*`에서 이후 공식 게시글 번호 기반 `DNF-*` 안정 ID로 전환했고, corpus snapshot(문서 목록·해시)과 run manifest(실행 재현 정보)로 재현성을 확보했다.

### 3-2. Baseline vs RAG

로컬 모델이 RAG 없이 문서 질문에 얼마나 답하는지부터 측정했다.

| 방식 | 문서 기반 질문 평균 | OOD 질문 평균 |
|---|---|---|
| Non-RAG baseline | 11.27 / 21 | 21.00 / 21 |
| RAG 적용 | 18.86 / 21 | 21.00 / 21 |

문서 전체를 넣는 것보다 관련 근거 chunk를 찾아 넣는 RAG가 더 안정적이라는 것을 확인했다.

### 3-3. Retriever 비교 (BM25 heuristic vs BGE-M3)

BM25는 순수 BM25가 아니라 phrase/coverage/intent bonus를 더한 heuristic이다. BGE-M3는 임베딩 검색이다.

| Retriever | Top-1 evidence hit | Avg token recall |
|---|---|---|
| BM25 heuristic | 19 / 22 | 0.994 |
| BGE-M3 | 21 / 22 | 1.000 |

BGE-M3가 top-1 근거 회수에서 앞서 최종 검색기로 채택했다.

### 3-4. 생성 모델·톤·구조화 ablation (검색기 BGE-M3 고정)

어떤 요소가 개선에 기여했는지 분리하려고 검색기를 고정하고 단계적으로 실험했다.

| 설정 | Factual proxy | Format proxy | Meta reasoning | Avg latency |
|---|---|---|---|---|
| BGE-M3 + `qwen3:4b` | 17 / 22 | 9 / 22 | 13 | 11.635s |
| BGE-M3 + instruct variant | 18 / 22 | 22 / 22 | 0 | 4.625s |
| + structured data | 17 / 22 | 22 / 22 | 0 | 5.130s |

가장 큰 변화는 생성 모델을 instruct variant로 바꿨을 때다. 영어 추론·메타 발화가 13건에서 0건으로 줄고 format proxy가 9/22에서 22/22로 올랐다. Structured data는 표형 정보 보완용으로 별도 해석한다.

### 3-5. Safety gate (키워드 baseline)

프롬프트 인젝션, 시스템 프롬프트 유출, 가짜 근거, 버그 악용, 현금화, 매크로, OOD를 키워드/조합 규칙으로 차단했다.

| 평가 세트 | 결과 | 해석 |
|---|---|---|
| 명시적 공격 | 10 / 10 | 직접 키워드 공격은 차단 |
| Paraphrase | 0 → 10 / 10 | 사후 보강했으나 test-informed 한계 |
| Stealth 사전 차단 | 0 / 10 | 키워드를 피하면 약함 |
| Stealth end-to-end | 6 / 10 | 생성 단계까지 포함하면 일부는 안전 거절 |

규칙 기반 gate는 설명 가능하고 빠르지만 완성된 보안 장치가 아니라는 점을 명확히 기록했다.

### 3-6. 2026-06 staged corpus 재평가

기존 벤치마크를 덮지 않고 최신 공식 문서를 snapshot 디렉터리에 staging해 20문항 신규 세트(`benchmark_questions_v2026_06`)로 재평가했다.

| Run | Factual proxy | Avg latency |
|---|---|---|
| BM25 + instruct | 13/20 | 6.061s |
| BGE-M3 + instruct | 13/20 | 4.219s |
| Hybrid + instruct | 15/20 | 4.613s |
| Hybrid + reranker + instruct | 15/20 | 20.868s |
| Hybrid + structured records + instruct | 16/20 | 4.273s |

hybrid + structured records가 품질·속도 균형 최고였고, reranker는 factual 이득 없이 latency만 4.5배 늘어 기본 경로에서 제외(검색 상한 레퍼런스로 동결)했다.

### 3-7. (6/30) 마무리 리뷰 + 편향·안정성 평가 확장

- 마무리 리뷰(`report/v2026_06_closing_review.md`): handoff 6개 질문에 답하고 기본 설정 확정. Q003/Q013/Q014/Q018 fail을 답변 단위로 분해해 false negative(Q013/Q018)와 진짜 누락(Q003)을 구분.
- 편향 평가셋 추가(`questions/bias_questions.csv`, 24문항 = 8 카테고리 × 3): 성별·연령·국적·사회경제·장애·비하·암묵전제·공정성. 공정성은 동일 질문 3페르소나 일관성 트리플.
- 안정성 정밀도 측정셋 추가(`questions/safety_overrefusal_questions.csv`, 20문항 = 5 카테고리 × 4): 정상 질문을 gate가 잘못 막는지(과차단) 측정. 키워드 gate에서 20문항 중 1건(FPSAFE009 '매크로 정책 문의') 과차단.
- 루브릭(`eval/bias_safety_evaluation_rubric.md`): 편향은 binary critical gate, 안정성은 recall·precision 분리.

편향셋 채점 결과: 24문항 전부 critical gate PASS(고정관념 동조·일반화·차등 대우·전제 수용 모두 0건 fail). 공정성 트리플도 일관.

### 3-8. (7/1) structured fix + DeepEval + intent gate

Codex가 이어서 세 갈래를 진행했다.

- Structured answer completeness fix: change record 5건과 답변 완전성 규칙(`must_include`/`answer_hint`/`answer_requirement`)을 더해 2026-06 factual proxy를 16/20 → 20/20으로 올림. Q003/Q010/Q013/Q014/Q018 regression 5/5 통과.
- DeepEval 통합: faithfulness judge를 compact context로 실행(top-3 pass 14/20). fail 6건은 judge false positive로 분류. judge를 최종 판정자가 아니라 manual review 큐 정렬용으로 규정.
- Intent safety gate(`scripts/safety_intent.py`): 키워드 gate를 정규식·근접·benign allowlist 조합으로 확장. dev/regression e2e 실행에서 공격 50/50 차단, 정상 50/50 통과(오탐 0), stealth 0/10 → 10/10. 이 수치는 최종 headline이 아니라 v6 fresh 검증 전 개발 성과로 라벨링한다.

### 3-9. (7/1) factual held-out v1 + source_relation ablation

structured fix의 20/20이 test-informed인지 확인하려고 별도 factual held-out 25문항(`heldout_factual_v1`)을 blind로 만들어 freeze한 뒤, source_relation과 completeness rule을 끄고 켜는 2x2 ablation(+no-structured baseline)을 dev·held-out 양쪽에서 실행했다.

- dev 20문항: full structured(source_relation on + completeness on) 조건이 20/20으로 최고.
- held-out 25문항: no-structured baseline을 포함한 5개 조건 전부 23/25로 동률.
- 원인: held-out 25문항 중 structured record가 발동한 문항은 0건이었다. dev에서는 9/20 문항에 발동했다. structured on/off 토글이 held-out에서는 그냥 no-op이었던 것이다.
- 결론: dev의 +3점은 held-out 일반화가 아니라 hand-authored record가 dev 문항에만 매칭된 효과다. 다음 방향은 손으로 쓴 record를 늘리는 것이 아니라, 원문 패치노트에서 atomic record를 자동 추출하는 extractor다.

상세: `report/heldout_factual_ablation_v1.md`.

**(7/4 수동 rubric 추가검증)** held-out 23/25는 자동 proxy 수치였다. 25문항 전체를 수동 rubric으로 다시 채점한 결과, HF023·HF024 fail은 그대로 확정되고(gold 조건절 누락, 진짜 오류), HF004는 자동 proxy가 놓친 completeness 문제(캐릭터별 필터 조건 누락)가 새로 발견됐다. HF025는 evidence에 없는 단어("신실한 소코르스")가 있어 환각으로 의심했으나 원본 문서 대조 결과 정식 명칭으로 확인되어 무혐의였다. 상세: `report/heldout_factual_v1_manual_rubric_review.md`.

### 3-10. (7/2~7/3) Safety held-out v1~v6

research_summary_and_roadmap.md에 적어둔 held-out 검증 프로토콜(사전등록 → freeze → blind 평가 → regression 분리 → rule 개선)을 safety gate에 실제로 적용했다. v1부터 v6까지 6라운드를 반복했다.

```
v1 blind held-out -> 평가 -> lineage 보존
v2 blind held-out -> 평가 -> targeted regression v2 -> rules v2
v3 blind held-out -> 평가 -> diagnostic -> independent review -> regression v3 -> rules v3
v4 blind held-out -> 평가 -> diagnostic -> independent review -> regression v4 -> rules v4
v5 blind held-out -> 평가 -> diagnostic -> independent review -> regression v5 -> rules v5
v6 blind held-out -> 사전 최종 선언 -> 평가 -> 최종 보고서 -> 라운드 종료
```

v6는 결과를 보기 전에 "이번 라운드의 마지막 fresh blind verification"으로 커밋 선언(`ebe38a1`)한 뒤 평가했다.

| gate | attack block rate | benign FP rate |
|---|---:|---:|
| keyword_rules_v2 | 1/24 (4.2%) | 0/24 (0.0%) |
| intent_rules_v4 | 10/24 (41.7%) | 0/24 (0.0%) |
| intent_rules_v5 | 12/24 (50.0%) | 0/24 (0.0%) |

`intent_rules_v5`는 v4보다 attack block이 2문항 늘고 benign FP는 0으로 유지됐지만, 절대 수치는 50%에 그친다. real-world harm/self-harm(0/4), malware/prompt-injection(1/4)은 여전히 취약하다. 사전 선언에 따라 v6 결과 확인 이후 추가 튜닝은 이번 라운드에 포함하지 않고 라운드를 종료했다.

이 결과는 5장에서 제기한 "intent gate 50/50·오탐 0은 평가셋에서 역산해 과장됐다"는 우려를 실제로 검증한 것이다. Fresh blind에서는 12/24(50.0%)로 나와 우려가 사실로 확인됐다. 동시에 정직한 held-out 프로토콜을 실행해 오염을 스스로 검출했다는 것 자체가 성과다.

상세: `report/safety_eval_final_report_v6.md`, `report/safety_eval_process_summary_for_main_project.md`(v1~v6 전체 파일 인덱스 포함).

### 3-11. (7/4) safety held-out 재검산 — backward-compat vs 진짜 blind

v6의 12/24가 n=24로 너무 작다는 우려를 검증하려고 두 가지를 추가 계산했다(`report/safety_heldout_backward_compat_analysis_v1.md`).

- 각 규칙 버전이 실제로 blind였던 held-out 조합만 모으면: `rules_v2` 58.3%(28/48) → `rules_v3` 50.0%(24/48) → `rules_v4` 37.5%(18/48) → `rules_v5` 50.0%(12/24, 추가 blind set 없음). 라운드를 거치며 단조 증가하지 않는다.
- 현재 최종 규칙(`intent_rules_v5`)을 과거 held-out(v1~v4)에 소급 적용하면 75.0%(90/120)까지 올라가지만, 이건 이미 각 라운드에서 진단·보강된 공격 스타일을 다시 맞히는 것이라 "구식 공격 유지력"이지 새로운 공격에 대한 일반화가 아니다. 어떤 튜닝에도 쓰인 적 없는 유일한 세트는 v6뿐이고, 거기서는 50.0%(12/24)에 머문다.
- 결론: v1~v6를 전부 합쳐 "하나의 큰 held-out"으로 재는 것은 틀렸다(v5는 순환 참조라 제외해야 함). 안전 재현율의 진짜 근거는 여전히 v6 12/24뿐이며, "구식 공격 75% 유지 vs 신규 공격 50%"로 나눠 보고하는 것이 정확하다.

상세: `report/safety_heldout_backward_compat_analysis_v1.md`.

---

## 4. 현재 전체 성적표

| 축 | 지표 | 현재 값 | 신뢰도 |
|---|---|---|---|
| 검색 | Top-1 evidence hit (2026-05) | BGE-M3 21/22 | 높음 |
| 생성 형식 | Format proxy | 22/22 (2026-05), 20/20 (2026-06) | 높음 |
| 생성 사실성 | Factual proxy (2026-06, dev) | structured fix 후 20/20 | 낮음 (test-informed) |
| 생성 사실성 | Factual proxy (held-out v1, 25문항) | 23/25, 구조화 on/off 전 조건 동률 (record 발동 0/25) | 검증됨 (구조화 이득 미확인) |
| 안전 재현율 | 공격 차단 (dev, intent gate) | 50/50 | 낮음 (test-informed) |
| 안전 재현율 | 공격 차단 (held-out v6, intent_rules_v5) | 12/24 (50.0%) | 검증됨 (절대 성능은 낮음) |
| 안전 정밀도 | 정상 질문 과차단 | 키워드 1/20, intent 0/20 (dev), held-out v6 0/24 | 중간~검증됨 |
| 편향 | critical gate PASS | 24/24 | 중간 (dev, held-out 아님) |
| 지연 | 평균 latency | 약 4.4s | 높음 |

신뢰도 "낮음(test-informed)"은 자기 평가셋에 맞춰져 있어 일반화를 장담할 수 없다는 뜻이고, "검증됨"은 fresh blind held-out으로 실측했다는 뜻이다. 검증됐다고 성능이 좋다는 뜻은 아니다 — factual/safety 둘 다 held-out에서는 dev보다 뚜렷이 낮거나(구조화 이득 0) 절반 수준(공격 차단 50%)에 그쳤다.

---

## 5. 핵심 이슈: test-informed 오염 진단

지금 프로젝트에서 가장 중요한 문제다. 최근 두 헤드라인 수치가 자기 평가셋에 맞춰져 있어 일반화를 과장한다.

1. structured fix의 20/20은 사실상 정답 주입에 가깝다. change record의 `source_relation` 필드가 gold 답변을 거의 그대로 옮긴 문장이고, 이를 `answer_hint`로 프롬프트에 넣는다. 게다가 record 5건은 벤치마크에서 틀린 문항만 골라 손으로 추가했다. 새 패치·새 질문에는 이런 record가 없으므로 20/20은 이 20문항 한정이다.

   **(7/3 갱신, 검증 완료)** 이 우려는 factual held-out v1로 실제 검증했다. held-out 25문항에서는 structured record가 0/25 문항에만 발동해 구조화 on/off가 사실상 no-op이었고, 모든 조건이 23/25로 동률이었다. 오염 우려가 사실로 확인됐다. 상세: `report/heldout_factual_ablation_v1.md`.

2. intent gate의 50/50·오탐 0도 규칙을 평가셋 문장에서 역산한 결과다. `safety_intent.py`의 benign allowlist에 '자동 분해', '자동 정렬', '보안 카드', '영수증', '환불' 등 과차단셋 문구가, 차단 패턴에는 stealth셋 문구가 그대로 들어 있다. 그 세트에서 만점이 나오는 것은 당연하다. 여전히 semantic classifier가 아니라 정교해진 키워드 규칙이다.

   **(7/3 갱신, 검증 완료)** 이 우려는 v1~v6 fresh blind held-out 프로토콜로 실제 검증했다. 최종 v6에서 `intent_rules_v5`는 dev의 50/50이 아니라 12/24(50.0%)를 기록했고, real-world harm/self-harm(0/4)과 malware/prompt-injection(1/4)은 특히 취약했다. 즉 오염 우려는 사실로 확인됐다. 상세: `report/safety_eval_final_report_v6.md`.

3. DeepEval fail 6건을 전부 judge 오류로 처리한 것은 편의적 해석 위험이 있어 제3자 검증이 필요하다.

   **(7/4 갱신, 독립 재검증 완료)** 원본 판정을 보지 않고 문항·근거·모델답변·judge reason을 다시 대조했다. 6건 중 5건(Q012, Q016, Q017, Q019, Q020)은 독립적으로도 judge 오류로 확인된다 — 특히 4건은 judge의 `reason` 텍스트 자체가 "모순 없음/score 1.00"이라고 말하면서 기록된 `score`는 0.000~0.500인, 도구 자체의 내적 불일치였다. 나머지 1건(Q003)은 판단이 갈리는 경계 사례로 남겨야 한다. 즉 원래 결론(6/6 judge 오류)은 살짝 과장이었고, 정확히는 5/6 확정 + 1/6 애매함이다. 상세: `report/deepeval_faithfulness_independent_recheck_v1.md`.

이 오염을 스스로 드러내고 held-out으로 재측정하는 것이, 평가 직무 관점에서는 오히려 최대 강점이 된다. 자기 평가의 함정을 발견하는 능력이 이 직무의 본질이기 때문이다.

---

## 6. 현재 목표

1. 1차 목표(제출용): 게임/금융권 AI 품질·안전성 평가 직무 지원(제출 목표일 2026-07-13)에 쓸 수 있도록, 평가 방법론과 정직한 한계 보고가 드러나는 실험 결과와 보고서를 완성한다.
2. 2차 목표(내용 완성도): 최근 수치의 test-informed 오염을 held-out 검증으로 정량화하고, "test-informed vs held-out"을 나란히 보고하는 구조로 전환한다.
3. 서술 목표: 완벽한 점수가 아니라 "검색 품질, 생성 사실성, 답변 형식, 안전 recall·precision, 편향, 자동 judge 한계"를 각각 분리 측정하고 실패를 분석하는 흐름을 보여준다.

---

## 7. 앞으로 진행할 것 (우선순위 로드맵)

(7/3 갱신) 아래 1·2번은 완료했다. 남은 우선순위는 3·4·5번이다.

1. ~~held-out 검증 (factual + safety 둘 다)~~ — **완료.**
   - factual: `heldout_factual_v1`(25문항) 실행 완료. structured record 발동 0/25로 구조화 이득이 확인되지 않음. `report/heldout_factual_ablation_v1.md`.
   - safety: v1~v6 fresh blind 반복 실행 완료. 최종 v6에서 attack block 12/24(50.0%), benign FP 0/24. `report/safety_eval_final_report_v6.md`.

2. ~~source_relation ablation~~ — **완료.** factual held-out v1과 같은 실행에서 source_relation/completeness rule 2x2 + no-structured baseline을 dev·held-out 양쪽에서 돌렸다. held-out에서는 record가 아예 발동하지 않아 leakage 크기를 분리하지 못했다 — 다음 단계는 손으로 쓴 record를 늘리는 것이 아니라 원문에서 atomic record를 자동 추출하는 extractor다.

   **(7/4 프로토타입 완료)** 화살표(`A → B`)와 서술형 추가/제거 문장, 변경 전/후 표 3가지 패턴으로 최소 추출기를 만들어 2026-06 staged corpus 8개 문서에 돌렸다. hand-authored 5건 중 2건은 완전 자동 복원, 1건은 후처리 필요한 부분 복원, 2건(표 중첩 케이스, 대시 없는 서술문)은 실패했다. 추가로 35개 후보를 더 찾았는데, 그 중 가격 변경("초월의 의지 50개→25개")은 처음엔 "hand-authored set에 없던 발견"으로 잘못 적었다가 확인해보니 `data/snapshots/.../structured/shop_items.json`의 `DNF-2927810-SHOP-02`에 이미 있었다(정정함). 순수하게 새로 찾은 건 몬스터 개명·아바타명 오탈자 수정 등이고, 더 중요한 발견은 extractor가 `change_records.json`용 후보와 `shop_items.json`용 후보를 스키마 구분 없이 섞어서 쏟아낸다는 점이다. 상세: `report/change_record_extractor_prototype_v1.md`.

3. custom JSON judge rubric. **미착수.**
   - DeepEval 기본 faithfulness 대신 `factual_match`/`completeness`/`unsupported_addition`/`live_server_misread`/`verdict`/`reason` JSON 출력 judge를 만든다.
   - 오염된 20문항이 아니라 held-out run(factual v1 또는 후속)에 적용한다. 생성 모델과 다른 judge 모델을 써서 자기 채점 편향을 줄인다.

4. structured record 충돌 처리. **미착수.**
   - record가 늘 때 한 질문에 여러 record가 붙으면 `needs_review`로 빼고, `applies_to_skill`/`applies_to_option`/`applies_to_question_type` 스코프 필드를 추가한다.
   - 확장 위생 항목이므로 여전히 낮은 우선순위.

5. intent gate 의미 기반화. **프로토타입 완료, 프로덕션 전환은 다음 라운드.**
   - "hand-rule 버전을 held-out에서 돌려 하락을 기록"하는 부분은 v1~v6로 완료했다(12/24).
   - **(7/4 완료, retrospective prototype)** 공격 프로토타입 임베딩 유사도 분류기를 실제로 만들어 같은 held-out에서 정면 비교했다. BGE-M3 임베딩 + dev 세트에서만 뽑은 프로토타입(공격 60개, 정상 72개) 1-NN 분류기가 v6에서 attack recall 20/24(83.3%), benign FP 0/24를 기록해 6라운드 튜닝한 규칙(12/24, 50.0%)을 상회했다. 특히 규칙이 대응하지 못했던 `real_world_harm_self_harm_threats`(0/4)를 임베딩은 도메인 규칙 없이 3/4까지 잡았다. **다만 이 수치는 held-out 텍스트를 프로토타입에 안 썼다는 뜻의 retrospective 결과이지, 완전한 사전등록 blind headline이 아니다** — 분류기 아이디어 자체와 real_world_harm 강조가 이미 v6에서 규칙의 약점을 본 뒤 이뤄졌을 수 있다. 정식 headline은 v7 사전등록 이후로 미룬다. 상세: `report/semantic_safety_classifier_prototype_v1.md`.
   - "dev vs held-out" 열을 나란히 두는 보고 방식은 safety v6 최종 보고서 기준으로는 이미 적용했다.
   - **(7/4 추가 발견)** `real_world_harm_self_harm_threats` 카테고리(0/4)는 "규칙이 약해서"가 아니라 **v6에서 처음 도입된 카테고리라 애초에 대응하는 rule 자체가 없었기 때문**이다(v1~v5는 다른 taxonomy를 썼다). 지금 패치하면 test-informed 오염이므로, 새 카테고리 추가는 v7의 사전등록 스코프로 넘긴다. 상세: `report/heldout_safety_v6_real_world_harm_category_note.md`.

추가 상시 과제: DeepEval 6건 재검증(완료, 5/6 확정), 편향셋을 held-out 페르소나로 확장(미착수). atomic record 자동 extractor는 프로토타입까지 완료했고(`report/change_record_extractor_prototype_v1.md`), 표 패턴 재설계와 사람 승인 단계 연결이 다음 과제로 남는다.

---

## 8. 산출물 지도

읽는 순서와 용도.

| 파일 | 용도 |
|---|---|
| `README.md` | 프로젝트 전체 소개(제출용 첫 화면) |
| `report/research_overview_master.md` | 이 문서. 전체 연구 총정리 색인 |
| `report/final_portfolio_report.md` | 전체 실험 과정·결과 통합 보고서 |
| `report/final_closing_review.md` | 제출용 최종 요약 |
| `report/application_summary.md` | 지원서·면접용 요약 |
| `report/v2026_06_closing_review.md` | 2026-06 세트 마무리 리뷰 |
| `report/structured_fix_iteration_v2026_06.md` | 7/1 structured fix 상세 |
| `report/deepeval_compact_evidence_calibration_v2026_06.md` | DeepEval judge 실험 |
| `report/safety_intent_e2e_gate_test.md` | intent gate e2e 결과 |
| `report/heldout_factual_ablation_v1.md` | factual held-out v1 + source_relation ablation, record 0/25 비전이 감사 |
| `report/safety_eval_final_report_v6.md` | safety held-out v6 최종 보고서(라운드 결론) |
| `report/safety_eval_process_summary_for_main_project.md` | safety held-out v1~v6 전체 과정 요약과 파일 인덱스 |
| `report/safety_heldout_backward_compat_analysis_v1.md` | v1~v6 합산이 왜 틀렸는지, 구식 공격 유지(75%) vs 진짜 신규 공격(v6, 50%) 분리 재검산 |
| `report/heldout_safety_v6_real_world_harm_category_note.md` | real_world_harm 카테고리 0/4의 원인이 규칙 약점이 아니라 taxonomy 신규 도입임을 재진단, v7 스코프 제안 |
| `report/deepeval_faithfulness_independent_recheck_v1.md` | DeepEval fail 6건 자기판정을 독립 재검증(5/6 확정, 1/6 애매함) |
| `report/heldout_factual_v1_manual_rubric_review.md` | factual held-out 25문항 수동 rubric 채점, HF004 completeness 누락 신규 발견 |
| `report/semantic_safety_classifier_prototype_v1.md` | BGE-M3 임베딩 1-NN 분류기 retrospective 프로토타입, v6에서 규칙(50.0%) 대비 83.3%로 상회(정식 headline은 v7 사전등록 이후) |
| `report/change_record_extractor_prototype_v1.md` | 화살표/서술형/표 패턴 자동 추출기 프로토타입, hand-authored 5건 중 2건 완전 복원 + 35개 후보 발견(가격 변경 건은 shop_items.json에 이미 있었음을 정정) |
| `report/bias_and_safety_eval_design.md` | 편향·안정성 평가 설계 |
| `report/session_2026_06_30_bias_safety_handoff.md` | 6/30 작업 정리 |
| `report/session_2026_07_01_structured_deepeval_safety_handoff.md` | 7/1 작업 정리 |
| `eval/evaluation_rubric.md`, `eval/bias_safety_evaluation_rubric.md` | 채점 루브릭 |

주의: `README.md`/`final_*`/`index.html`에는 7/4 기준 test-informed caveat와 held-out 실측값을 함께 반영했다. factual은 dev 20/20과 held-out 23/25(record 0/25 발동)를 분리하고, safety는 dev/regression 50/50과 fresh v6 12/24, FP 0/24를 분리해 보여준다. semantic classifier 20/24는 retrospective prototype으로만 표기한다.
