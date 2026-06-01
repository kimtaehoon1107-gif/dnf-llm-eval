# 던전앤파이터 문서 기반 LLM 평가 포트폴리오 최종 보고서

## 1. 프로젝트 목적

이 프로젝트는 넥슨 게임 도메인 LLM 평가 어시스턴트 직무를 목표로, 던전앤파이터 공식 업데이트 문서를 기반으로 로컬 LLM의 답변 품질을 평가하는 과정을 구현한 것이다.

핵심 목표는 단순 챗봇 구현이 아니라, 패치노트와 공지 문서에서 실제 유저가 물어볼 수 있는 질문을 만들고, 답변 정확성, 근거 충실성, 환각 억제, 범위 통제, 서비스 톤을 기준으로 평가 체계를 설계하는 것이다.

## 2. 데이터 수집과 전처리

Selenium 기반 수집 스크립트로 던전앤파이터 업데이트 목록을 렌더링한 뒤, `li.title`의 `data-no`와 `data-url`을 읽어 상세 공지 URL을 구성했다. 이후 상세 페이지 본문을 Markdown으로 저장하고 문서별 metadata를 CSV로 관리했다.

초기에는 일반적인 `a href` 링크를 찾는 방식으로 접근했지만, 던파 업데이트 목록은 제목 `li` 태그에 글 번호가 들어 있는 구조였다. 이 문제를 디버그 HTML과 CSV로 확인한 뒤, 실제 페이지 구조에 맞는 수집기로 수정했다.

## 3. 벤치마크 설계

공식 문서를 기준으로 문서 기반 질문 22개, 게임 외 범위 질문, 프롬프트 공격 질문을 구성했다. 질문 유형은 단순 사실 확인, 조건 판단, 비교, 범위 제한, 표 기반 질의가 섞이도록 설계했다.

평가 루브릭은 7개 항목으로 구성했다.

| 항목 | 평가 의도 |
|---|---|
| 정확성 | 문서 기준 사실이 맞는가 |
| 근거 충실성 | 답변이 공식 문서 근거에 기반하는가 |
| 완전성 | 기간, 조건, 제한, 예외를 빠뜨리지 않았는가 |
| 의도 적합성 | 유저 질문의 초점에 맞게 답했는가 |
| 환각 억제 | 문서에 없는 내용을 만들지 않았는가 |
| 범위 통제 | 게임 외 질문과 공격성 질문을 제한하는가 |
| 표현 품질 | 실제 게임 서비스 답변처럼 읽히는가 |

이 기준은 RAGAS의 context relevance, faithfulness, answer relevance 관점과 HELM의 다차원 평가 관점을 참고해 게임 운영 문서 평가에 맞게 재구성했다. RAGAS 라이브러리를 직접 실행한 것은 아니며, 평가 구조를 설계할 때 참고 기준으로 사용했다.

## 4. 시스템 구조

최종 시스템은 다음 흐름으로 구성했다.

```text
Question
→ Safety Gate
→ Retriever
→ Context Builder
→ Generator LLM
→ Logger
→ Evaluator
→ Report
```

| 단계 | 구현 내용 |
|---|---|
| Safety Gate | 게임 외 질문, prompt injection, 허위 근거 유도, 악용 요청 차단 |
| Retriever | BM25 heuristic baseline과 BGE-M3 dense retrieval 비교 |
| Context Builder | 검색 chunk와 structured shop data 결합 |
| Generator | `qwen3:4b`, `qwen3:4b-instruct-2507-q4_K_M` 비교 |
| Logger | question_id, retrieved_chunk_ids, answer, latency, status 저장 |
| Evaluator | 검색 지표, 답변 proxy, 수동 rubric 평가 |

## 5. 주요 실험 결과

### 5.1 Baseline vs RAG

초기 baseline은 RAG 없이 문서 기반 질문에 답하게 한 방식이었다. 이 방식은 간단하지만 최신 패치노트의 세부 조건과 표형 정보를 안정적으로 찾지 못했다.

| 방식 | 전체 평균 | 문서 기반 질문 평균 | OOD 질문 평균 |
|---|---:|---:|---:|
| Non-RAG baseline | 13.87 / 21 | 11.27 / 21 | 21.00 / 21 |
| RAG 적용 | 19.43 / 21 | 18.86 / 21 | 21.00 / 21 |

RAG 적용 후 문서 기반 질문 평균은 11.27점에서 18.86점으로 개선됐다.

### 5.2 검색기 비교

22개 문서 기반 질문에 대해 BM25 heuristic과 BGE-M3를 비교했다. BM25 heuristic은 순수 BM25가 아니라 phrase/coverage/intent bonus를 더한 키워드 중심 검색 baseline이다.

| Retriever | Top-8 evidence hit | Top-1 evidence hit | Avg token recall |
|---|---:|---:|---:|
| BM25 heuristic | 22 / 22 | 19 / 22 | 0.994 |
| BGE-M3 | 22 / 22 | 21 / 22 | 1.000 |

BGE-M3는 top-1 근거 적중에서 더 좋았다. 모든 검색기가 top-8 안에는 정답 근거를 포함했기 때문에, 이후 병목은 검색 자체보다 답변 생성 품질에 가까웠다.

### 5.3 답변 생성 비교

동일한 `qwen3:4b` 모델에 검색기별 근거를 넣어 답변을 생성하고 proxy 지표로 비교했다.

| 설정 | Factual proxy | Format proxy | Meta reasoning | Avg latency |
|---|---:|---:|---:|---:|
| BM25 heuristic + `qwen3:4b` | 17 / 22 | 0 / 22 | 22 | 8.964s |
| BGE-M3 + `qwen3:4b` | 19 / 22 | 0 / 22 | 21 | 9.063s |

BGE-M3는 factual proxy를 개선했지만, `qwen3:4b`는 영어식 추론 과정과 메타 발화를 출력했다. 즉, 검색 개선만으로는 서비스 답변 형식 문제가 해결되지 않았다.

### 5.4 최종 생성 모델 개선

최종 실험에서는 검색기를 BGE-M3로 고정하고, 구조화 데이터와 서비스 톤 프롬프트를 붙인 뒤 `qwen3:4b-instruct-2507-q4_K_M`을 사용했다.

이 모델을 선택한 이유는 세 가지다. 첫째, 4.0B 규모의 Qwen3 계열 모델이라 개인 PC에서 재현 가능한 경량 로컬 실험이라는 프로젝트 목적에 맞다. 둘째, `Q4_K_M` 양자화 모델이므로 모델 크기와 실행 부담을 줄일 수 있다. 셋째, 기존 `qwen3:4b`에서 드러난 영어 추론 과정과 메타 발화 문제를 줄이기 위해 instruction following이 더 안정적인 instruct variant가 필요했다.

따라서 최종 모델 선택은 단순히 더 큰 모델을 고른 것이 아니라, `BGE-M3가 근거를 찾고`, `structured data가 표형 정보를 보완하며`, `qwen3:4b-instruct-2507-q4_K_M이 근거를 한국어 서비스 답변으로 정리하는` 역할 분리 전략이었다.

| 설정 | Factual proxy | Format proxy | Meta reasoning | Avg latency |
|---|---:|---:|---:|---:|
| BGE-M3 + `qwen3:4b` | 19 / 22 | 0 / 22 | 21 | 9.063s |
| BGE-M3 + structured + `qwen3:4b-instruct-2507` | 18 / 22 | 22 / 22 | 0 | 5.435s |

최종 조합은 factual proxy가 1문항 낮아졌지만, 서비스 답변 형식은 22/22로 개선됐다. 영어 추론 과정과 메타 발화가 사라졌고 평균 응답 시간도 줄었다.

### 5.5 구조화 데이터 개선

상점표 질문은 일반 chunk 검색만으로 `아이템명-가격-구매 제한` 관계를 안정적으로 보존하기 어려웠다. 이를 해결하기 위해 DOC-01, DOC-02의 켈돈 자비 상점 표를 `data/structured/shop_items.json`으로 추출했다.

구조화 데이터 실험은 전체 22문항이 아니라 상점표 관련 Q001~Q004에 한정한 부분 ablation이다. 대표적으로 Q003에서 BGE-M3만 사용할 때는 가격 120개 정보가 누락됐지만, BGE-M3+structured 설정에서는 가격과 월 4회 제한을 함께 회수했다.

### 5.6 안전성 평가

게임 외 질문, 프롬프트 탈취, 문서 조작, 버그 악용, 매크로 자동화 요청을 포함한 공격 세트를 구성했다. 안전 게이트 적용 후 local baseline과 RAG 시스템 모두 10개 공격 질문을 10개 모두 차단했다.

안전 게이트는 차단 유형을 `prompt_leakage`, `fake_evidence`, `exploit_request`, `automation_abuse`, `out_of_domain` 등으로 기록하도록 구성했다. 다만 현재 safety gate는 규칙 기반 1차 필터이므로, paraphrase 공격과 정상 질문 오탐에 대한 추가 검증이 필요하다.

이 한계를 확인하기 위해 기존 공격 의도를 다른 표현으로 바꾼 paraphrase 공격 세트 10문항을 추가했다. 최초 safety gate는 paraphrase 세트를 0/10만 차단했지만, 복합 조건 규칙을 추가한 뒤 10/10 차단으로 개선했다. 다만 이는 규칙 기반 개선이므로 완전한 의미 기반 방어로 보지는 않는다.

또한 StruQ와 Instruction Hierarchy의 instruction/data 분리 관점을 참고해 prompt template을 보완했다. 검색 근거와 구조화 근거를 `읽기 전용 데이터`로 표시하고, 시스템 규칙과 답변 규칙이 사용자 질문 및 검색 문서보다 높은 우선순위임을 명시했다. 향후에는 Llama Guard처럼 입력과 출력을 별도 safeguard classifier로 검사하는 구조를 추가할 수 있다.

## 6. 대표 수동 채점 결과

자동 proxy 지표의 한계를 보완하기 위해 대표 문항 수동 채점표를 만들었다.

| 파일 | 내용 |
|---|---|
| `eval/representative_manual_scoring.csv` | 대표 문항별 7개 루브릭 점수 |
| `report/representative_manual_scoring.md` | 실패 원인과 개선 효과 해석 |

핵심 발견은 세 가지다.

1. BGE-M3는 BM25 heuristic보다 의미 기반 top-1 근거 회수에 강했다.
2. 상점표처럼 셀 관계가 중요한 문서는 구조화 데이터가 필요했다.
3. 기존 `qwen3:4b`는 사실 근거를 받아도 최종 서비스 답변 형식 제어가 약했다.

## 7. 직무 연결성

| 공고 요구 | 프로젝트 대응 |
|---|---|
| 게임 도메인 LLM 벤치마크 구성 | DNF 업데이트 문서 기반 질문 22개와 공격 질문 세트 설계 |
| 평가 지표 및 기준 개발 | 7개 루브릭과 0~3점 스코어링 체계 설계 |
| LLM 응답 품질 평가 | baseline, RAG, BGE-M3, structured data, 생성 모델 비교 |
| 결과 분석 및 공유 | 실패 유형, 개선 효과, 다음 개선 방향 보고서화 |
| 데이터 기반 문제 분석 | 검색 hit, factual proxy, format proxy, 수동 채점 결합 |

## 8. 한계와 다음 개선

| 한계 | 개선 방향 |
|---|---|
| 표형 정보 혼입 | structured record 우선 규칙 또는 answer template 추가 |
| 자동 proxy 오판 | 수동 채점 확대 또는 LLM-as-judge 추가 |
| BM25 heuristic 영향 | 순수 BM25 점수를 별도 산출해 검색 비교를 더 엄밀하게 검증 |
| reranker 미적용 | BGE-M3 top-k 결과에 cross-encoder reranker 추가 |
| Safety gate 일반화 한계 | paraphrase 공격과 정상 질문 오탐 세트를 추가해 규칙 기반 필터 보완 |
| 서비스 호칭 톤 미반영 | `모험가님` 호칭을 명시한 서비스 톤 프롬프트 재실험 |
| 문서 수 5개 중심 | 더 많은 패치노트, 이벤트, 가이드 문서로 확장 |

## 9. 결론

이 프로젝트의 결론은 “가벼운 로컬 LLM도 게임 문서 QA에 사용할 수 있지만, 문서 검색, 구조화 데이터, 안전 게이트, 평가 루브릭이 함께 있어야 한다”이다.

특히 RAG는 baseline보다 문서 기반 질문 성능을 크게 개선했고, BGE-M3는 BM25 heuristic보다 top-1 근거 회수를 높였다. 최종적으로 `BGE-M3 + structured data + qwen3:4b-instruct-2507-q4_K_M + service-tone prompt` 조합이 현재 제출용으로 가장 일관된 결과를 보였다.

## 10. 참고문헌

상세 참고문헌은 `report/references.md`에 정리했다. 핵심 근거는 HELM의 multi-metric evaluation, RAGAS/ARES의 retrieval-generation 분리 평가, FActScore의 factuality 평가, BGE-M3의 다국어 dense retrieval, Qwen3의 다국어 경량 모델군, StruQ와 Instruction Hierarchy의 instruction/data 분리, Llama Guard와 OWASP LLM Top 10의 safeguard 관점이다.
