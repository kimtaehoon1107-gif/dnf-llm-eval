# 던전앤파이터 문서 기반 LLM 평가 프로젝트 최종 리뷰

## 1. 초록

본 프로젝트는 던전앤파이터 공식 업데이트 문서를 기반으로 로컬 LLM의 답변 품질을 평가한 포트폴리오 프로젝트다. 목표는 단순 챗봇 구현이 아니라, 게임 도메인 문서 수집, 벤치마크 질문 설계, RAG 검색, 구조화 데이터 보완, 안전성 게이트, 생성 모델 비교, 평가 지표 설계, 오류 분석까지 이어지는 평가 파이프라인을 만드는 것이다.

최종 결과는 다음과 같다. RAG 적용 후 문서 기반 질문 평균은 11.27/21에서 18.86/21로 개선되었다. 검색기 비교에서는 BGE-M3가 BM25 heuristic보다 높은 top-1 evidence hit를 보였다. 기존 `qwen3:4b`는 factual proxy는 높았지만 영어 추론과 메타 발화를 출력해 format proxy가 0/22였고, `qwen3:4b-instruct-2507-q4_K_M` 적용 후 format proxy는 22/22로 개선되었다.

## 2. 연구 목적

넥슨 게임 도메인 LLM 평가 어시스턴트 직무와 연결되는 목표는 다음과 같다.

| 직무 요구 | 프로젝트 대응 |
|---|---|
| 게임 도메인 LLM 벤치마크 구성 | 던파 업데이트 문서 기반 질문 22개, OOD 질문, adversarial 질문 설계 |
| 평가 지표 및 기준 개발 | 검색 지표, 답변 proxy, 7개 수동 rubric 설계 |
| LLM 응답 품질 평가 | baseline, RAG, BM25, BGE-M3, structured data, 생성 모델 비교 |
| 결과 분석 및 공유 | CSV 로그와 Markdown 보고서로 결과 정리 |

핵심 질문은 다음과 같다.

1. 로컬 경량 LLM만으로 최신 게임 문서 질문에 답할 수 있는가?
2. RAG를 붙이면 문서 기반 정확성이 얼마나 개선되는가?
3. 키워드 검색 BM25와 dense 검색 BGE-M3 중 어떤 방식이 더 적합한가?
4. 표형 데이터는 일반 chunk 검색만으로 충분한가?
5. 검색 근거가 좋아도 최종 답변 형식이 서비스 품질에 맞는가?
6. 게임 외 질문, 프롬프트 공격, 허위 근거 유도는 통제되는가?

## 3. 데이터 및 벤치마크

Selenium 기반 수집기로 던전앤파이터 업데이트 목록 페이지를 렌더링하고, `li.title`의 `data-no`와 `data-url`을 이용해 상세 공지 URL을 구성했다. 이후 본문을 Markdown으로 저장하고 문서 ID, 제목, URL, 저장 경로를 metadata로 관리했다.

주요 산출물은 다음과 같다.

| 경로 | 설명 |
|---|---|
| `data/processed_md/` | 수집한 업데이트 문서 Markdown |
| `data/metadata.csv` | 문서 ID, 제목, URL, 저장 경로 |
| `data/structured/shop_items.json` | 켈돈 자비 상점표를 행 단위로 구조화한 JSON |
| `questions/benchmark_questions.csv` | 문서 기반 평가 질문 22개 |
| `questions/out_of_domain_questions.csv` | 게임 외 질문 |
| `questions/adversarial_questions.csv` | 공격성 및 환각 유도 질문 |

`benchmark_questions.csv`의 `doc_id`는 사용자가 입력하는 값이 아니라, 평가자가 정답 출처를 추적하기 위해 붙인 메타데이터다.

## 4. 평가 설계

본 프로젝트는 RAGAS 라이브러리를 직접 사용하지 않았다. 대신 RAGAS, ARES, vRAG-Eval, HELM의 평가 관점을 참고해 검색 품질과 답변 품질을 분리했다.

| 평가 영역 | 지표 |
|---|---|
| 검색 품질 | top-k evidence hit, top-1 evidence hit, token recall, phrase hit ratio |
| 답변 자동 평가 | factual proxy, format proxy, meta reasoning flag, Korean character ratio |
| 수동 평가 | 정확성, 근거 충실성, 완전성, 의도 적합성, 환각 억제, 범위 통제, 표현 품질 |

자동 proxy는 모델 간 차이를 빠르게 보기 위한 기준이다. 다만 사람이 보면 정답인 답변도 token 기준에서 실패할 수 있으므로, 최종 판단에는 대표 문항 수동 채점을 함께 사용했다.

## 5. 시스템 구조

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
| Safety Gate | prompt injection, 허위 근거 유도, 게임 외 질문, 악용성 질문 차단 |
| Retriever | BM25 heuristic과 BGE-M3 비교. 최종 검색기는 BGE-M3 |
| Context Builder | 검색 chunk와 structured shop data 결합 |
| Generator LLM | `qwen3:4b`, `qwen3:4b-instruct-2507-q4_K_M` 비교 |
| Logger | question_id, retrieved_chunk_ids, answer, latency, status 저장 |
| Evaluator | 검색 지표, 답변 proxy, 수동 rubric 평가 |

## 6. 실험 설정

| 실험 | 설정 | 목적 |
|---|---|---|
| Non-RAG baseline | `qwen3:4b` | RAG 없이 로컬 모델의 한계 확인 |
| Retriever 비교 | `qwen3:4b + BM25 heuristic/BGE-M3` | 키워드 검색과 dense 검색 비교 |
| Structured ablation | `qwen3:4b + BGE-M3 + structured` | 상점표 행 단위 정보 보완 효과 확인 |
| Safety 평가 | `safety-gate + adversarial set` | 공격성 질문 및 범위 밖 질문 차단 확인 |
| 최종 모델 실험 | `BGE-M3 + structured + qwen3:4b-instruct-2507 + service-tone` | 서비스 답변 형식 개선 확인 |

초기 retriever 비교에서는 `--restrict-to-question-doc`를 사용했다. 이는 실제 서비스용 옵션이 아니라, 정답 문서 안에서의 검색과 답변 생성 능력을 분리해 보기 위한 평가용 ablation이다. 최종 실험에서는 이 제한을 제거하고 전체 문서 corpus에서 검색했다.

## 7. 결과

### 7.1 Baseline vs RAG

| 방식 | 전체 평균 | 문서 기반 질문 평균 | OOD 질문 평균 |
|---|---:|---:|---:|
| Non-RAG baseline | 13.87 / 21 | 11.27 / 21 | 21.00 / 21 |
| RAG 적용 | 19.43 / 21 | 18.86 / 21 | 21.00 / 21 |

RAG 적용 후 문서 기반 질문 성능이 크게 개선되었다. 이는 최신 게임 문서 QA에서는 모델의 사전지식보다 공식 문서 검색과 근거 제공이 중요하다는 점을 보여준다.

### 7.2 검색기 비교

| Retriever | Top-8 evidence hit | Top-1 evidence hit | Avg token recall |
|---|---:|---:|---:|
| BM25 heuristic | 22 / 22 | 19 / 22 | 0.994 |
| BGE-M3 | 22 / 22 | 21 / 22 | 1.000 |

BGE-M3가 top-1 evidence hit에서 더 안정적이었기 때문에 최종 검색기로 선택했다. 이때 BM25 baseline은 순수 BM25가 아니라 phrase/coverage/intent bonus가 포함된 BM25 heuristic이므로, 더 엄밀한 검색 비교에서는 순수 BM25 점수를 별도로 산출할 수 있다.

### 7.3 답변 생성 비교

| 설정 | Factual proxy | Format proxy | Meta reasoning | Avg latency |
|---|---:|---:|---:|---:|
| BM25 heuristic + `qwen3:4b` | 17 / 22 | 0 / 22 | 22 | 8.964s |
| BGE-M3 + `qwen3:4b` | 19 / 22 | 0 / 22 | 21 | 9.063s |
| BGE-M3 + structured + `qwen3:4b-instruct-2507` | 18 / 22 | 22 / 22 | 0 | 5.435s |

기존 `qwen3:4b`는 factual proxy가 높았지만 영어 추론과 메타 발화를 출력했다. 반면 `qwen3:4b-instruct-2507-q4_K_M`은 factual proxy가 1문항 낮아졌지만 format proxy를 22/22로 개선했고, 평균 응답 시간도 줄었다.

최종 모델은 "가장 큰 모델"이 아니라 "제한된 게임 문서 QA에 맞는 경량 instruct 모델"로 선택했다. 로컬 `ollama show` 기준 이 모델은 Qwen3 architecture, 4.0B parameters, Q4_K_M quantization을 사용한다. 따라서 BGE-M3와 structured data가 최신 문서 근거를 제공하고, `qwen3:4b-instruct-2507-q4_K_M`은 그 근거를 서비스 답변 형식으로 정리하는 역할을 맡는다. 이 선택은 로컬 실행 가능성, 한국어 답변 형식 안정성, 평균 응답 시간, 재현성을 함께 고려한 결과다.

### 7.4 구조화 데이터

구조화 데이터 실험은 전체 22문항 비교가 아니라, 상점표와 직접 관련된 Q001~Q004만 대상으로 한 부분 ablation이다.

| 설정 | 평가 범위 | 질문 수 | Factual proxy | Format proxy |
|---|---|---:|---:|---:|
| BGE-M3 only | 전체 벤치마크 | 22 | 19 / 22 | 0 / 22 |
| BGE-M3 + structured | 상점표 관련 Q001~Q004 | 4 | 3 / 4 | 0 / 4 |

구조화 데이터는 `태초 소울 1개 상자`처럼 가격과 구매 제한이 같은 표에 붙어 있는 질문에서 필요한 값을 함께 회수하는 데 도움이 되었다.

## 8. 오류 분석

### Q002: 인접 행 조건 혼입

Q002의 정답 근거는 `태초 광휘의 의지 / 광휘의 잔영 790개 / 계정당 1회`다. 모델은 가격과 계정 제한은 맞혔지만, 바로 아래 상품인 `태초 소울 1개 상자`의 `월 4회`, `이월` 조건을 함께 붙였다. 이는 chunk 근거와 structured 근거가 함께 제공될 때 generator가 인접 행 정보를 혼합할 수 있음을 보여준다.

### Q016: 자동 proxy의 한계

Q016 답변은 `라이브 서버 HP는 90, 성화 작열 감소 HP는 30이다`로 사실상 정답이다. 그러나 token recall 기준에서는 factual proxy 실패로 잡혔다. 자동 지표는 빠른 비교에는 유용하지만, 최종 판단에는 수동 rubric 또는 LLM-as-judge가 필요하다.

### 서비스 톤

최종 모델은 한국어 공식 안내체와 형식 통제에는 성공했다. 다만 모든 답변을 `모험가님`으로 시작하는 던파식 호칭 톤은 아직 강하게 반영하지 않았다. 이는 후속 개선으로 제시하는 편이 자연스럽다.

### Safety gate paraphrase test

기존 safety gate는 원래 adversarial 질문 10/10은 차단했지만, 같은 공격 의도를 다른 표현으로 바꾼 paraphrase 세트에서는 0/10만 차단했다. 이후 단일 키워드가 아니라 여러 단서가 함께 등장할 때 차단하는 복합 조건 규칙을 추가했고, paraphrase 세트와 기존 공격 세트 모두 10/10 차단으로 개선했다. 다만 이는 여전히 규칙 기반 1차 필터이므로 정상 질문 오탐과 새로운 우회 표현에 대한 검증이 필요하다.

추가로 StruQ와 Instruction Hierarchy의 관점을 참고해 prompt template에서 검색 근거를 `읽기 전용 데이터`로 표시하고, 시스템 규칙 > 답변 규칙 > 사용자 질문 > 검색 근거의 우선순위를 명시했다. Llama Guard식 input-output safeguard classifier는 후속 개선으로 남겼다.

## 9. 한계 및 후속 개선

| 한계 | 개선 방향 |
|---|---|
| 표형 정보 혼입 | structured record 우선 규칙 또는 answer template 추가 |
| 자동 proxy 오판 | 수동 채점 확대 또는 LLM-as-judge 추가 |
| BM25 heuristic 영향 | 순수 BM25 점수를 별도 산출해 검색 비교를 더 엄밀하게 검증 |
| reranker 미적용 | BGE-M3 top-k 결과에 cross-encoder reranker 추가 |
| Safety gate 일반화 한계 | paraphrase 공격과 정상 질문 오탐 세트를 추가해 규칙 기반 필터 보완 |
| 서비스 호칭 톤 미반영 | `모험가님` 톤 프롬프트 추가 후 재평가 |
| 문서 수 5개 중심 | 더 많은 패치노트, 이벤트, 가이드 문서로 확장 |

## 10. 최종 결론

본 프로젝트는 게임 문서 기반 LLM 평가에서 발생하는 문제를 검색, 구조화 근거, 생성 모델, 안전성, 평가 지표로 분리해 검증했다.

최종 결론은 다음과 같다.

1. RAG는 최신 게임 문서 질문에서 baseline 대비 성능을 크게 개선했다.
2. BGE-M3는 BM25 heuristic보다 top-1 근거 회수 성능이 높았다.
3. 상점표처럼 행 단위 관계가 중요한 문서는 구조화 데이터 보완이 필요했다.
4. 기존 `qwen3:4b`는 사실성은 개선했지만 서비스 답변 형식에는 부적합했다.
5. `qwen3:4b-instruct-2507-q4_K_M`은 format proxy 22/22, meta reasoning 0건으로 답변 형식 문제를 해결했다.
6. Safety gate는 기존 adversarial 질문 10/10을 차단했고, paraphrase test에서 드러난 약점을 복합 조건 규칙으로 보완했다. 다만 현재 방식은 규칙 기반 1차 필터라 정상 질문 오탐과 새로운 우회 표현 검증이 추가로 필요하다.

한 문장으로 요약하면, 본 프로젝트는 `게임 문서 기반 질문을 만들고, 검색-생성-안전성-평가를 분리해 로컬 LLM 답변 품질을 체계적으로 비교한 평가 중심 포트폴리오`다.

## 11. 참고문헌

평가 방법, 검색 모델, 생성 모델, safety 설계 근거는 `report/references.md`에 모았다. 본 프로젝트에서는 RAGAS, ARES, FActScore, HELM을 평가 설계 참고문헌으로 사용했고, BGE-M3와 Qwen3는 검색 및 생성 모델 선정 근거로, StruQ, Instruction Hierarchy, Llama Guard, OWASP LLM Top 10은 prompt injection과 safeguard 설계 근거로 사용했다.
