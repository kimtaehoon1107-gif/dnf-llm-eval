# 서비스 톤 개선 가이드

작성일: 2026-05-29

## 1. 목적

문서 기반 QA의 1차 목표는 정확성과 근거성이다. 하지만 실제 게임 서비스에서 사용할 수 있는 답변이 되려면 표현도 중요하다. 이 프로젝트에서는 던전앤파이터 유저를 `모험가님`으로 보고, 공식 안내에 가까운 서비스 톤을 별도 옵션으로 실험한다.

핵심은 말투를 부드럽게 만드는 것이 아니라, 모험가가 오해 없이 바로 행동할 수 있도록 답변 구조를 개선하는 것이다.

## 2. 적용 방식

LoRA나 파인튜닝은 사용하지 않고, 프롬프트로 제어한다. 초기에는 few-shot 예시도 함께 넣었지만, qwen3:4b 로컬 실행에서는 latency가 크게 증가해 기본값에서 제외했다.

이유는 다음과 같다.

- 현재 목표는 모델 학습보다 응답 품질 평가와 개선 실험이다.
- 말투는 지식 학습보다 출력 형식 제어에 가깝다.
- 고품질 답변 데이터가 충분히 쌓이기 전에는 LoRA보다 프롬프트 실험이 재현성과 비용 면에서 적합하다.
- 실제 질의응답 속도를 고려해 최종 권장 프로필은 `RAG + safety gate + fast-service-profile`이다.
- `--service-tone`과 `--service-tone-examples`는 말투 실험용 옵션으로 남긴다.

## 3. 서비스 톤 규칙

`--service-tone` 옵션을 켜면 짧은 서비스 톤 규칙만 추가한다.

- 사용자는 던전앤파이터 모험가이며, 필요할 때 `모험가님`으로 자연스럽게 지칭한다.
- 공식 안내처럼 정확하고 조심스럽게 답한다.
- 신규/복귀 유저도 이해할 수 있도록 쉬운 표현을 쓴다.
- 첫 문장에 핵심 답변을 먼저 말한다.
- 수치, 조건, 기간, 제한이 2개 이상이면 짧은 bullet로 나눈다.
- 퍼스트 서버나 테스트 성격의 내용은 라이브 서버 확정처럼 단정하지 않는다.
- 친절한 표현을 쓰더라도 문서에 없는 추천, 추측, 미래 예측, 개인 의견은 추가하지 않는다.
- 불필요한 인사말이나 잡담은 하지 않는다.

`--service-tone-examples` 옵션을 함께 켜면 few-shot 예시도 추가된다. 다만 qwen3:4b에서는 응답 시간이 크게 늘 수 있어 기본 실행에는 권장하지 않는다.

## 4. 평가 기준

서비스 톤은 기존 루브릭의 `표현 품질`을 더 세분화해 본다.

| 항목 | 확인 내용 |
|---|---|
| 핵심 선제시 | 첫 문장에서 질문의 답을 바로 말하는가 |
| 조건 구분 | 수치, 기간, 제한 조건을 보기 쉽게 나누는가 |
| 공식 안내 톤 | 단정, 과장, 개인 추천 없이 조심스럽게 말하는가 |
| 유저 친화성 | 신규/복귀 모험가도 이해하기 쉬운가 |
| 근거 보존 | 말투 개선 과정에서 문서 밖 내용을 추가하지 않는가 |

서비스 톤 점수가 높아도 정확성, 근거성, 환각 방지 점수가 낮으면 좋은 답변으로 보지 않는다. 톤은 품질 보조 항목이며, 정답성과 근거성을 대체하지 않는다.

## 5. 실행 방법

Baseline에 서비스 톤 적용:

```powershell
python scripts\run_local_llm_eval.py `
  --model qwen3:4b `
  --service-tone `
  --output eval\local_llm_service_tone_sample.csv `
  --limit 5
```

RAG에 서비스 톤 적용:

```powershell
python scripts\run_rag_local_llm_eval.py `
  --model qwen3:4b `
  --questions questions\service_tone_sample_questions.csv `
  --restrict-to-question-doc `
  --safety-gate `
  --fast-service-profile `
  --output eval\rag_local_llm_fast_no_tone_sample.csv
```

말투 실험을 별도로 보고 싶을 때:

```powershell
python scripts\run_rag_local_llm_eval.py `
  --model qwen3:4b `
  --questions questions\service_tone_sample_questions.csv `
  --restrict-to-question-doc `
  --safety-gate `
  --service-tone `
  --fast-service-profile `
  --output eval\rag_local_llm_service_tone_light_sample.csv
```

## 6. 면접 설명 포인트

면접에서는 다음처럼 설명할 수 있다.

> RAG로 정답성과 근거성을 개선한 뒤, 실제 서비스 응답에 가까워지도록 서비스 톤 실험을 추가했습니다. 던전앤파이터 유저를 `모험가님`으로 보고, 핵심 답변 선제시, 조건/수치 분리, 퍼스트 서버 단정 방지, 문서 밖 추측 금지를 짧은 프롬프트 규칙으로 제어했습니다. few-shot은 latency가 커져 실험 옵션으로만 남겼고, LoRA는 고품질 답변 데이터가 충분히 축적된 이후 고려할 후속 개선안으로 두었습니다.

## 7. 샘플 실행 결과

`questions/service_tone_sample_questions.csv`의 3개 질문을 대상으로 속도와 말투를 비교했다.

```powershell
python scripts\run_rag_local_llm_eval.py `
  --model qwen3:4b `
  --questions questions\service_tone_sample_questions.csv `
  --restrict-to-question-doc `
  --safety-gate `
  --fast-service-profile `
  --output eval\rag_local_llm_fast_no_tone_sample.csv
```

측정 결과:

| 설정 | 3문항 총 latency | 평균 latency | 해석 |
|---|---:|---:|---|
| RAG + fast profile, no service tone | 41.36초 | 13.79초 | 속도와 답변 품질 균형이 좋음 |
| RAG + fast profile + lightweight service tone | 38.64초 | 12.88초 | 속도는 유사하고 답변 문장성이 일부 개선 |
| RAG + service tone + few-shot | 114.78초 | 38.26초 | 말투 실험용으로만 적합 |

결론적으로 qwen3:4b 로컬 환경에서는 few-shot 예시를 길게 추가하는 것보다, 기본 답변 규칙을 간결하게 유지하고 RAG context를 줄이는 편이 실제 게임 질문 응답에 더 적합하다. 짧은 `--service-tone` 규칙은 속도 부담이 크지 않아 선택적으로 사용할 수 있다.

서비스 톤은 답변을 과하게 장식하기보다, 핵심 답변 선제시와 조건 분리를 유도하는 정도로만 적용한다. `모험가님` 호칭은 모든 답변에 강제로 넣지 않고, 주의사항이나 안내가 필요한 경우에만 자연스럽게 쓰도록 유지한다.
