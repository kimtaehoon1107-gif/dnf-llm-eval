# BGE-M3 기반 생성 설정 Ablation Study

## 목적

기존 최종 조합은 `BGE-M3 + structured data + qwen3:4b-instruct-2507-q4_K_M`을 한 번에 적용한 통합 시스템 설정이었다. 이 방식은 제출용 최종 품질을 확인하는 데는 유용하지만, 어떤 요소가 어떤 개선에 기여했는지 분리해 설명하기 어렵다.

따라서 본 실험에서는 검색기를 BGE-M3로 고정하고, 생성 모델 변경이 답변 형식과 지연 시간에 어떤 영향을 주는지 비교했다. 구조화 데이터의 효과는 별도 structured data/probe 실험에서 해석한다.

## 공통 조건

| 항목 | 설정 |
|---|---|
| 질문 세트 | `questions/benchmark_questions.csv` 22문항 |
| 검색기 | BGE-M3 |
| 검색 범위 | 전체 5개 문서 corpus |
| Top-k | 8 |
| Thinking | disabled |
| 출력 예산 | `--num-predict 512` |
| Safety gate | 문서 기반 QA 비교이므로 미적용 |

`--restrict-to-question-doc`는 사용하지 않았다. 즉, 이번 ablation은 정답 문서로 검색 범위를 제한하지 않고 전체 문서 corpus에서 검색한 결과다.

## 실험 설정

| 단계 | 설정 | 목적 |
|---:|---|---|
| 1 | BGE-M3 + `qwen3:4b` | 기존 base 생성 모델의 한계 확인 |
| 2 | BGE-M3 + `qwen3:4b-instruct-2507-q4_K_M` | 모델만 instruct variant로 바꿨을 때 효과 확인 |

## 결과

| 설정 | Factual proxy | Format proxy | Meta reasoning | Avg latency |
|---|---:|---:|---:|---:|
| BGE-M3 + `qwen3:4b` | 17 / 22 | 9 / 22 | 13 | 11.635s |
| BGE-M3 + `qwen3:4b-instruct-2507` | 18 / 22 | 22 / 22 | 0 | 4.625s |

## 해석

가장 큰 변화는 `qwen3:4b`에서 `qwen3:4b-instruct-2507-q4_K_M`으로 바꿨을 때 발생했다. 모델만 바꿔도 format proxy가 9/22에서 22/22로 개선되고, meta reasoning 출력은 13건에서 0건으로 줄었다. 평균 응답 시간도 11.635초에서 4.625초로 줄었다.

이 결과에서 가장 큰 병목은 검색기가 아니라 생성 모델의 답변 형식이었다. BGE-M3가 근거를 찾아도 기본 `qwen3:4b`는 영어 추론 과정과 메타 발화를 자주 노출했다. instruct variant로 바꾸자 format proxy와 meta reasoning 지표가 동시에 안정화됐다.

구조화 데이터의 효과는 전체 22문항 평균보다 상점표 관련 Q001~Q004 또는 2026-06 structured record probe처럼 record가 실제 발동하는 조건에서 해석하는 것이 타당하다. 이 보고서의 핵심 결론은 모델 변경 효과이며, structured data의 일반화 여부는 `heldout_factual_ablation_v1.md`와 `structured_record_probe_v1.md`에서 별도로 다룬다.

## 실패 문항 관찰

| 설정 | Factual proxy 실패 문항 |
|---|---|
| BGE-M3 + `qwen3:4b` | Q001, Q005, Q011, Q017, Q020 |
| BGE-M3 + instruct | Q003, Q005, Q014, Q016 |

Q016처럼 사람이 보면 사실상 정답인 답변도 자동 factual proxy에서는 실패로 잡힐 수 있다. 따라서 factual proxy는 빠른 비교용 보조 지표이며, 최종 품질 판단에는 수동 rubric 또는 LLM-as-a-Judge 보조 평가가 필요하다.

## 결론

이번 ablation으로 최종 조합의 핵심 개선 원인은 `qwen3:4b-instruct-2507-q4_K_M`의 답변 형식 안정화와 latency 개선에 있음을 분리해 확인했다. 구조화 데이터는 표형 정보 보완을 위한 별도 구성 요소지만, factual proxy 결과만으로 전체 일반화 효과를 단정하지 않는다.

최종 제출용 해석은 다음과 같다.

> BGE-M3는 근거 검색을 담당하고, qwen3 instruct variant는 한국어 답변 형식과 meta reasoning 억제를 담당한다. Structured data는 상점표처럼 행 단위 관계가 중요한 문서에서 보완 근거로 사용한다. Factual proxy는 자동 근사 지표이므로 false negative 가능성을 함께 보고, 대표 문항은 수동 rubric으로 재확인한다.
