# Held-out Factual Ablation v1

## 요약

2026-06 structured RAG 개선 결과를 dev/test-informed 숫자로만 해석하지 않기 위해, 별도 factual held-out 세트를 먼저 freeze한 뒤 source_relation과 completeness rule의 2x2 ablation을 실행했다.

핵심 결론은 다음과 같다.

- dev 20문항에서는 full structured 조건이 20/20으로 가장 높다.
- held-out 25문항에서는 no-structured baseline을 포함한 모든 조건이 23/25로 동일하다.
- 따라서 이번 held-out 결과만으로는 source_relation 또는 completeness rule의 held-out 일반화 우위를 주장하지 않는다.
- 이 결과는 실패가 아니라, dev에서 좋아진 숫자가 held-out에서도 같은 방식으로 분리되는지 검증한 감사 결과다.

## 프로토콜

- 라벨링: 기존 20/20, 50/50, 24/24 headline 결과는 dev/test-informed이며 held-out 일반화 성능으로 해석하지 않는다는 caveat를 먼저 추가했다. 커밋: `170e25f`.
- held-out 제작: `questions/heldout_factual_v1.csv`는 원문 `processed_md` 패치노트만 보고 작성했다. gold answer는 evidence 문장과 교차검증했고, evidence 조각이 원문에 존재하는지 기계 검증했다.
- freeze: `questions/heldout_factual_v1.csv`와 `questions/heldout_factual_v1.manifest.json`을 ablation 전에 단독 커밋했다. 커밋: `eede285`.
- ablation 구현: `scripts/run_rag_local_llm_eval.py`에 `--disable-structured-source-relation`, `--disable-structured-completeness-rules` 플래그를 추가했다. 커밋: `5146b9d`.
- 결과 확인 후 `change_records.json`, `safety_intent.py`, 프롬프트, threshold, judge, held-out 질문/gold는 수정하지 않았다.

## 실행 조건

- 모델: `qwen3:4b-instruct-2507-q4_K_M`
- Retriever: `hybrid`
- 질문셋:
  - dev: `questions/benchmark_questions_v2026_06.csv` 20문항
  - held-out: `questions/heldout_factual_v1.csv` 25문항
- 공통 옵션: `--disable-thinking --num-predict 512 --num-ctx 8192`
- 채점: `scripts/score_answer_runs.py`의 factual proxy와 format proxy

## 결과

| 조건 | structured | source_relation | completeness rule | dev factual proxy | held-out factual proxy | 해석 |
|---|---:|---:|---:|---:|---:|---|
| no-structured baseline | off | n/a | n/a | 17/20 | 23/25 | dev에서는 구조화 근거가 이득이지만 held-out에서는 baseline도 동일권 |
| atomic only, completeness off | on | off | off | 19/20 | 23/25 | dev +2, held-out 차이 없음 |
| atomic only, completeness on | on | off | on | 19/20 | 23/25 | completeness 단독 held-out 이득 없음 |
| full hint, completeness off | on | on | off | 19/20 | 23/25 | source_relation 단독 held-out 이득 없음 |
| full hint, completeness on | on | on | on | 20/20 | 23/25 | dev 최고점, held-out에서는 다른 조건과 동률 |

모든 조건에서 format proxy는 dev 20/20, held-out 25/25였다.

### held-out에서 조건이 평탄한 이유 (record 발동 0/25)

held-out 모든 조건이 23/25로 동일한 것은 우연이 아니다. held-out 답변 로그의 `structured_record_ids`를 확인한 결과, **held-out 25문항 중 structured record가 발동한 문항은 0건**이다. 즉 held-out에서는 structured on/off 토글이 no-op이었고, 그래서 조건 간 차이가 나타날 수 없었다.

이것은 "구조화 RAG 기법이 held-out에서 효과가 없다"가 아니라, **"손으로 만든 structured record가 dev 벤치마크 문항에는 붙지만, blind로 만든 새 문항 25개에는 하나도 매칭되지 않는다"**는 뜻이다. record는 dev에서 9/20 문항에 발동했고(unique record id 7개: `change_records.json`의 hand-authored 5건 + `shop_items.json`의 기존 상점 record 2건), held-out에서는 0/25 문항에 발동했다. 이 차이는 이 프로젝트에서 관찰한 test-informed 오염을 가장 직접적으로 정량화한 수치다.

따라서 dev의 structured 이득(+3)은 held-out 일반화가 아니라 dev 문항에 매칭된 hand-authored record 효과로 해석하는 편이 안전하다. 구조화 RAG가 기법으로서 일반화되는지는 이 실험으로 답하지 못했으며, 그것을 확인하려면 held-out 문항에 대해서도 blind로 작성했거나 자동 추출한 record가 발동하는 조건에서 재측정해야 한다.

## 실패 패턴

held-out 실패는 모든 조건에서 `HF023`, `HF024`로 반복됐다.

- `HF023`: 모델은 필사의 저지에서 로페즈 즉시 조우 경로 추가는 답했지만, 중간보스를 생략할 수 있는 게이트가 열린다는 조건을 생략했다.
- `HF024`: 모델은 총 3개 게이트 생략 가능은 답했지만, 1개의 게이트가 추가되었다는 변경점을 생략했다.

두 문항 모두 모든 조건에서 실패했으므로, 이번 source_relation/completeness ablation의 차이라기보다 원문 chunk 기반 답변의 세부 완전성 문제로 보는 것이 더 적절하다.

dev 실패 중 `Q012`는 여러 조건에서 반복됐다. 모델은 12초에서 9초로 변경되는 핵심은 답했지만, gold의 "공격력 11.5% 감소 조건 유지"를 생략했다. `Q010`의 no-structured 실패는 모델 답변이 실질적으로 정답에 가까운 proxy false negative 가능성이 있다. 단, 이번 보고에서는 proxy 결과를 수정하지 않고 그대로 둔다.

## 해석 규칙

- held-out 25문항에서는 1~2문항 차이로 우열을 단정하지 않는다.
- 이번 결과는 조건 간 held-out 차이가 0문항이므로 동률권이다.
- dev에서는 full structured가 no-structured 대비 +3문항이지만, dev/test-informed 세트이므로 headline 일반화 성능으로 쓰지 않는다.
- 제출용 표현은 "full structured가 held-out에서 우월하다"가 아니라 "dev 개선을 held-out으로 검증했고, held-out에서는 구조화 조건 간 차이가 관찰되지 않았다"가 맞다.

## 산출물

- `questions/heldout_factual_v1.csv`
- `questions/heldout_factual_v1.manifest.json`
- `eval/ablation_source_relation_summary.csv`
- `eval/ablation_source_relation_detail.csv`
- `eval/ablation_v2026_06_*_answers.csv`
- `eval/ablation_v2026_06_*_answers.manifest.json`

## 후속

- safety held-out은 이번 마감 스코프에서 실행하지 않았다. 후속으로 keyword gate와 intent gate를 같은 held-out 공격 문항에서 비교한다.
- custom judge validation은 이번 마감 스코프에서 실행하지 않았다. 후속으로 held-out 일부에 대해 사람 판정과 judge 판정 일치율을 별도 지표로 보고한다.
- ablation 진단상 source_relation의 held-out 우위가 분리되지 않았으므로, 다음 구조화 개선은 손으로 쓴 source_relation을 늘리는 방향보다 원문에서 atomic field를 자동 추출하는 extractor로 가는 편이 더 정당하다.
