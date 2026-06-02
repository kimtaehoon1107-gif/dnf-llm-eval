# Baseline 및 Ablation 실험 설계

작성일: 2026-05-28

## 1. Baseline이 의미하는 것

이 프로젝트의 baseline은 `naive full-document context baseline`이다.

동작 방식은 다음과 같다.

```text
질문 CSV의 doc_id 확인
→ 해당 doc_id의 Markdown 문서 1개 로드
→ 문서 전체 또는 앞부분 12,000자 입력
→ qwen3:4b가 답변 생성
```

즉, 질문마다 연결된 문서 1개를 모델에게 통째로 제공하고 답하게 하는 방식이다. 검색 단계는 없다.

## 2. 왜 이런 baseline을 두는가

이 방식은 실제 서비스 구조로는 단순하지만, 비교 실험에서는 의미가 있다.

- 문서를 줬을 때도 경량 LLM이 긴 문서에서 필요한 근거를 잘 찾는지 확인할 수 있다.
- RAG가 단순히 문서를 더 많이 넣어서 좋아진 것이 아니라, 관련 chunk를 찾아 넣어서 좋아졌는지 비교할 수 있다.
- 구현 복잡도가 낮아 재현 가능한 하한선 역할을 한다.
- 이후 RAG, safety gate, 구조화 데이터 변환의 개선 효과를 단계적으로 보여줄 수 있다.

따라서 면접이나 README에서는 그냥 `baseline`이라고만 말하기보다 `검색 없는 naive full-document baseline`이라고 설명하는 편이 좋다.

## 3. 현재 비교 구조

| 단계 | 설명 | 목적 |
|---|---|---|
| No-context/OOD | 문서 없이 범위 밖 질문 거절 | 도메인 제한 지시가 작동하는지 확인 |
| Full-document baseline | 질문 doc_id의 문서 1개를 통째로 입력 | 긴 문서 안에서 모델이 스스로 근거를 찾는지 확인 |
| RAG | 질문 관련 chunk를 검색해 입력 | 검색 보강이 정확도와 근거성을 높이는지 확인 |
| RAG + safety gate | 공격성 요청을 검색 전에 차단 | RAG가 관련 없는 chunk를 근거로 오답 생성하는 문제 방지 |
| RAG + structured data | 표형 상점 데이터를 JSON record로 보강 | 가격, 구매 제한, 이월처럼 줄 단위 표에서 섞이는 수치 관계 보강 |

## 4. 현재 결과 해석

문서 기반 질문 평균은 다음과 같이 개선됐다.

```text
Full-document baseline: 11.27 / 21
RAG: 18.86 / 21
개선폭: +7.59
```

이 결과는 경량 로컬 LLM이 긴 문서를 통째로 받았을 때는 핵심 근거를 놓치거나 환각할 수 있지만, 관련 chunk를 검색해 제공하면 답변 품질이 크게 개선된다는 점을 보여준다.

공격성 질문에서는 다른 양상이 나왔다.

```text
RAG prompt-only: 9 / 10 거절
RAG + safety gate: 10 / 10 사전 차단
```

즉, RAG는 문서 QA 정확도에는 유리하지만 공격성 질문에서는 검색 전에 안전 필터가 필요하다.

## 5. 후속으로 추가하면 좋은 비교군

시간이 더 있다면 다음 비교군을 추가할 수 있다.

| 비교군 | 기대 효과 |
|---|---|
| No-context LLM | 모델 자체 지식만으로 답하려는 환각 경향 확인 |
| BM25 heuristic RAG vs BGE-M3 embedding RAG | 키워드 검색과 의미 검색의 차이 비교 |
| RAG top-k 변화 | 검색 chunk 수가 정확도와 환각에 미치는 영향 분석 |
| 표 데이터 JSON 변환 RAG | 구현 완료, Q002~Q004 검색 근거 보강 확인 |
| 다른 경량 모델 비교 | qwen3:4b 선택 근거 강화 |

현재 포트폴리오에서는 `full-document baseline`, `RAG`, `RAG + safety gate`만으로도 평가 설계와 개선 분석을 보여주기에는 충분하다.
