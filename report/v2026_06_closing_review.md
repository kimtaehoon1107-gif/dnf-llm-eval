# 2026-06 Staged Corpus 평가 마무리 리뷰

작성일: 2026-06-30
후속 업데이트: 2026-07-01 structured fix 결과 반영
대상 브랜치: `codex/v2026-06-results`
기준 커밋: `5fff72b Add structured v2026_06 change records`
질문셋: `benchmark_questions_v2026_06` (20문항, staged corpus `dnf-official-updates-2026-06-staged`)

## 1. 목적

이 문서는 2026-06 staged corpus에서 진행한 retriever/생성 비교 실험을 마무리하고, 다음 작업으로 넘어가기 전에 결과 해석과 의사결정을 확정하기 위한 리뷰다. handoff 문서(`CLAUDE_REVIEW_CONTEXT_v2026_06`)가 남긴 6개 검토 질문에 답하는 형태로 정리한다.

## 2. 결과 요약

`eval/v2026_06_answer_compare_summary.csv` 기준이다.

| Run | Factual proxy | Format proxy | Refusal | Avg gold token recall | Avg latency |
|---|---:|---:|---:|---:|---:|
| BM25 + instruct | 13/20 | 20/20 | 3 | 0.553 | 6.061s |
| BGE-M3 + instruct | 13/20 | 20/20 | 3 | 0.505 | 4.219s |
| Hybrid + instruct | 15/20 | 20/20 | 2 | 0.550 | 4.613s |
| Hybrid + BGE reranker + instruct | 15/20 | 20/20 | 0 | 0.577 | 20.868s |
| Hybrid + structured records + instruct | 16/20 | 20/20 | 0 | 0.597 | 4.273s |
| Hybrid + structured fix + instruct | 20/20 | 20/20 | 0 | - | 4.399s |

핵심 관찰:

- Hybrid가 단일 retriever(BM25, BGE-M3)보다 factual proxy와 token recall 모두 높다.
- Reranker는 검색 품질 지표(token recall 0.577)는 올리지만 factual proxy는 hybrid와 동일한 15/20이고, latency가 4.6s에서 20.9s로 약 4.5배 늘었다.
- Structured records는 factual proxy 16/20, token recall 0.597로 최고이면서 latency는 4.273s로 가장 빠른 축에 든다.
- 2026-07-01 structured fix에서는 snapshot shop record, change record 5건, 답변 완전성 규칙을 더해 factual proxy와 format proxy가 모두 20/20이 됐다. 상세 내역은 `report/structured_fix_iteration_v2026_06.md`를 기준으로 본다.

## 3. 검토 질문에 대한 답

### Q1. `hybrid + structured records`를 2026-06 평가의 기본값으로 둘 만한가?

그렇다. 6/30 기준으로도 같은 instruct 모델 위에서 factual proxy 최고(16/20), token recall 최고(0.597), refusal 0, latency 최저급(4.273s)을 동시에 만족하는 유일한 설정이었다. 7/1 structured fix 이후에는 factual proxy가 20/20까지 올라, 2026-06 staged corpus의 기본 생성 경로로 둘 근거가 더 강해졌다. 다만 "기본값"이라는 표현은 두 가지 의미를 분리해서 기록하는 것이 정확하다.

- 자동 proxy 기준 best 설정: `hybrid + structured fix`.
- 검색 품질 상한 참조용: `hybrid + reranker`. 답변 proxy 이득은 없지만 top-1 evidence hit 19/20으로 retriever 능력의 천장을 보여주는 진단 지표로 남긴다.

결론은 reranker를 기본 생성 경로에서 빼고 검색 품질 레퍼런스로만 유지하라는 Codex 권고와 동일하다. 6/30의 16 대 15 차이는 표본 크기상 "동률 이상이면서 비용이 더 싸다"로 해석하는 것이 맞았고, 7/1 후속 fix는 그 structured 경로를 더 정밀하게 다듬었을 때의 개선 여지를 보여준다.

### Q2. structured record 매칭 규칙이 충분히 안전한가, 더 엄격해야 하는가?

현재 규칙(옵션명 + before/after 수치 또는 대상 스킬+필드가 모두 맞을 때만 record 주입)은 방향이 옳다. Q011(일반 타이드 바운드 쿨타임)이 질풍 옵션 전용 record(12초→9초)를 상속하지 않고 정답(20초→18초)을 내는 것이 그 증거다.

다만 지금 안전성은 "규칙이 보수적이라서"가 아니라 "변경 record가 2건뿐이라서" 확보된 면이 크다. record가 수십 건으로 늘면 옵션명만 같고 맥락이 다른 충돌이 생길 수 있다. 권장 보강은 다음과 같다.

- record에 적용 스코프 필드(`applies_to_skill`, `applies_to_option`, `applies_to_question_type`)를 명시해 매칭을 데이터로 통제한다.
- 한 질문에 2개 이상 record가 매칭되면 자동 주입을 막고 `needs_review` 플래그로 빼낸다. 조용히 둘 다 주입하는 것이 가장 위험하다.
- record 주입 여부와 record id를 답변 로그(`structured_record_ids`)에 이미 남기고 있으므로, 매칭이 실제로 정답에 기여했는지 사후 검증을 정례화한다.

즉 규칙 로직 자체보다 record가 늘었을 때의 충돌 처리와 관측 가능성을 먼저 갖추는 것이 안전하다.

### Q3. Q003 / Q013 / Q014 / Q018을 token/phrase factual proxy의 false negative로 봐야 하는가?

실제 답변을 직접 대조한 결과 네 건은 성격이 다르다. 한 덩어리로 false negative 처리하면 안 된다.

| 문항 | gold 대비 모델 답변 | 판정 |
|---|---|---|
| Q013 | `'격랑' 개화 옵션 / 훅 샷 / 15.8% → 17.6%`를 모두 포함. 표현만 다름 | 명백한 false negative. proxy의 phrase 분할 매칭 한계 |
| Q018 | `48로 수정됩니다`. 질문이 이미 "115레벨 앵커 무기 최대 내구도"를 명시했고 핵심 수치는 정확 | false negative. 주어 생략으로 token recall이 낮게 잡힘 |
| Q014 | `'모두 받기' 버튼이 추가됩니다`. 핵심은 맞지만 `아라드 나침반`, `일괄 획득` 누락 | 경계 사례. 사실은 맞으나 완전성 감점. proxy fail은 과하지만 만점도 아님 |
| Q003 | `필요 재료가 삭제되며`로 일반화. gold의 `프라임 스텔라 10개`를 특정하지 못함 | 진짜 부분 정답. false negative 아님. 완전성 미달이 맞음 |

정리하면 Q013, Q018은 false negative로 분류해 manual 또는 LLM-as-judge에서 PASS 처리해야 한다. Q014는 "정확하나 불완전"으로 부분 점수, Q003은 부분 정답으로 둔다. 이렇게 나누면 실제 factual 정답률은 자동 proxy의 16/20보다 높고(Q013, Q018 추가) Q003/Q014는 완전성 개선 과제로 남는다.

이 분석 자체가 포트폴리오의 강점 포인트다. "자동 지표가 16/20이라고 끝내지 않고, 4건의 fail을 답변 단위로 열어 false negative와 진짜 누락을 분리했다"는 흐름은 평가 담당자가 보여줘야 할 핵심 역량이다.

후속 structured fix에서는 이 분류를 그대로 작업 단위로 삼았다. Q003/Q014는 구조화 record와 답변 완전성 규칙으로 보강했고, Q013/Q018은 대상 명시와 관계 표현을 강화했다. 추가로 Q010도 regression에 포함해 서비스 제거 관계를 고정했다. 결과적으로 Q003, Q010, Q013, Q014, Q018 regression은 5/5를 통과했다.

### Q4. 짧은 한국어 패치 QA에 현실적인 rubric 또는 LLM-as-judge 설계는?

기존 `eval/evaluation_rubric.md`의 6항목 + 4 critical gate 구조를 그대로 재사용하되, 자동화 가능한 형태로 좁힌 LLM-as-judge를 권장한다.

- 입력: 질문, gold_answer, evidence, 모델 답변.
- 출력(JSON 고정): `factual_match`(0/1), `completeness`(0/1/2), `unsupported_addition`(0/1, 환각 게이트), `live_server_misread`(0/1), `verdict`(pass/partial/fail), `reason`(한 문장).
- 판정 규칙: `unsupported_addition=1` 또는 `live_server_misread=1`이면 점수와 무관하게 fail. 이는 기존 binary critical gate 철학과 일치한다.
- 신뢰성 확보: 같은 답변을 자동 token proxy와 LLM-judge 양쪽으로 채점하고 불일치 문항만 사람이 본다. judge가 token proxy를 대체하는 게 아니라, 불일치 triage 도구로 쓴다.

판정 모델은 생성 모델(qwen3:4b instruct)과 다른 모델을 쓰는 것이 자기 채점 편향을 줄인다. 로컬 제약이 있으면 더 큰 로컬 모델이나 외부 API를 judge로 두고, 일치율(judge vs human)을 별도 지표로 보고한다.

### Q5. reranking에 계속 투자할지, structured extraction과 answer judging으로 옮길지?

후자로 옮기는 것을 권장한다. 근거는 비용 대비 효과다. reranker는 latency를 4.5배 늘리고 factual proxy 이득은 0이었다. 반면 structured records는 더 싸게 동률 이상을 냈고, Q3에서 본 false negative 문제는 retriever가 아니라 채점 쪽 문제다. 즉 지금 병목은 "근거를 못 찾는 것"이 아니라 "맞는 답을 자동 지표가 틀렸다고 보는 것"이다. 따라서 reranker는 검색 상한 레퍼런스로 동결하고, 노력은 (1) structured extraction 확장, (2) LLM-as-judge 도입에 배분한다.

### Q6. 패치 변경 질문에 answer template을 추가하는 것이 좋은가, 벤치마크 과적합인가?

답변 출력단 template(예: "X는 A에서 B로 변경됩니다" 고정 틀)은 권하지 않는다. 20문항 벤치마크에 맞춘 출력 틀은 전형적인 과적합이고, 새 패치 문장 구조가 조금만 달라도 깨진다. 대신 입력단 구조화(structured records)에 계속 투자하는 것이 일반화에 유리하다. record는 "무엇이 정답 근거인가"를 데이터로 공급할 뿐 출력 문장을 고정하지 않으므로, 모델이 표현을 자연스럽게 생성하면서 근거만 정확해진다. template이 필요하다면 출력이 아니라 평가 rubric 쪽에 "before/after 쌍이 모두 있는가"를 명시 항목으로 넣는 방식이 안전하다.

## 4. 마무리 의사결정

- 2026-06 기본 설정: `hybrid + structured fix + qwen3:4b-instruct-2507-q4_K_M`로 확정.
- reranker: 검색 품질 상한 레퍼런스로 동결. 기본 생성 경로 제외.
- false negative 및 완전성 이슈: Q003, Q010, Q013, Q014, Q018을 후속 regression으로 묶어 5/5 통과 확인.
- 다음 단계: structured record 충돌 처리 보강, LLM-as-judge triage 도입.
- 표본 한계: 20문항 기준이므로 1~2문항 차이는 우열 단정 대신 "동률 이상 + 저비용" 프레임으로 보고한다.

## 5. 다음 작업으로의 연결

이 마무리 이후 평가 축을 품질(factual/format)에서 안전성과 공정성으로 확장한다. 구체적으로 (1) safety gate의 미탐(stealth)과 과차단(false positive)을 분리 측정하고, (2) 편향 평가셋을 추가한다. 상세 설계는 `report/bias_and_safety_eval_design.md`를 참고한다.
