# 던전앤파이터 문서 기반 LLM 평가 프로젝트 최종 리뷰

## 1. 초록

본 프로젝트는 던전앤파이터 공식 업데이트 문서를 기반으로 로컬 LLM의 답변 품질을 평가한 포트폴리오 프로젝트다. 목표는 단순 챗봇 구현이 아니라, 게임 도메인 문서 수집, 벤치마크 질문 설계, RAG 검색, 구조화 데이터 보완, 안전성 게이트, 생성 모델 비교, 평가 지표 설계, 오류 분석까지 이어지는 평가 파이프라인을 만드는 것이다.

최종 결과는 다음과 같다. RAG 적용 후 문서 기반 질문 평균은 11.27/21에서 18.86/21로 개선되었다. 검색기 비교에서는 BGE-M3가 BM25 heuristic보다 높은 top-1 evidence hit를 보였다. 추가 ablation에서는 BGE-M3를 고정한 상태에서 `qwen3:4b`의 format proxy가 9/22였고 meta reasoning 출력이 13건 발생했지만, `qwen3:4b-instruct-2507-q4_K_M` 적용 후 format proxy는 22/22, meta reasoning은 0건으로 개선되었다.

2026-07-01 후속 실험에서는 2026-06 staged corpus 20문항을 추가해 `hybrid + structured fix + qwen3:4b-instruct-2507-q4_K_M` 설정을 검증했다. Snapshot 구조화 근거와 답변 완전성 규칙을 보강한 뒤 factual proxy와 format proxy가 모두 20/20을 통과했다. DeepEval faithfulness는 compact top-3 evidence 기준 자동 pass 14/20이었지만, 독립 재검증에서 5/6건은 judge 오류 또는 reason-score 불일치로 확인했고 Q003은 경계 사례로 남겼다. 이후 diagnostic/probe에서는 record가 실제 발동하는 조건에서 no-structured 24/35, atomic records 30/35, structured fix 32/35를 기록해 구조화 메커니즘 자체와 record coverage 문제를 분리했다. Safety는 개발용 regression과 fresh held-out을 분리했고, 최종 v6에서 intent_rules_v5가 12/24 attack recall, benign FP 0/24를 기록했다.

주의: 위 2026-07-01 structured fix 및 intent safety gate 결과는 dev/test-informed 결과다. 동일 문항의 실패 분석을 바탕으로 record와 rule을 보강한 뒤 재측정했으므로 headline 수치를 held-out 일반화 성능으로 해석하지 않는다. 이후 factual blind held-out 25문항을 freeze해 재검증한 결과, structured record는 dev 9/20 문항에 발동했지만 held-out에서는 0/25 문항에 발동했고 모든 ablation 조건이 23/25로 동률이었다. Structured record probe는 held-out 일반화 근거가 아니라 record 발동 조건의 메커니즘 진단으로만 해석한다. Safety도 regression 24/24가 아니라 사전 선언한 v6 12/24를 최종 fresh 결과로 보고한다. Semantic classifier의 v6 20/24는 retrospective prototype이므로 future work로 둔다.

## 2. 연구 목적

게임 도메인 LLM 평가/AI 서비스 품질 및 안전성 평가 직무와 연결되는 목표는 다음과 같다.

| 직무 요구 | 프로젝트 대응 |
|---|---|
| 게임 도메인 LLM 벤치마크 구성 | 던파 업데이트 문서 기반 질문 22개, OOD 질문, adversarial 질문 설계 |
| 평가 지표 및 기준 개발 | 검색 지표, 답변 proxy, legacy 수동 rubric, binary critical gate 설계 |
| LLM 응답 품질 평가 | baseline, RAG, BM25, BGE-M3, structured data, 생성 모델 비교 |
| 결과 분석 및 공유 | CSV 로그와 Markdown 보고서로 결과 정리 |

핵심 질문은 다음과 같다.

1. 로컬 경량 LLM만으로 최신 게임 문서 질문에 답할 수 있는가?
2. RAG를 붙이면 문서 기반 정확성이 얼마나 개선되는가?
3. 키워드 검색 BM25와 dense 검색 BGE-M3 중 어떤 방식이 더 적합한가?
4. 표형 데이터는 일반 chunk 검색만으로 충분한가?
5. 검색 근거가 좋아도 최종 답변 형식이 사용자에게 바로 보여줄 수 있는 수준인가?
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
| 생성 설정 ablation | `BGE-M3` 고정 후 모델과 structured 근거를 단계적으로 비교 | 변수별 개선 효과 분리 |
| 최종 통합 설정 | `BGE-M3 + structured + qwen3:4b-instruct-2507` | 답변 형식과 표형 정보 보완을 함께 확인 |

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

### 7.3 답변 생성 ablation

검색기를 BGE-M3로 고정하고 전체 5개 문서 corpus에서 검색한 뒤, 생성 모델과 구조화 데이터 효과를 단계적으로 비교했다. 이 실험에서는 `--restrict-to-question-doc`를 사용하지 않았다.

| 설정 | Factual proxy | Format proxy | Meta reasoning | Avg latency |
|---|---:|---:|---:|---:|
| BGE-M3 + `qwen3:4b` | 17 / 22 | 9 / 22 | 13 | 11.635s |
| BGE-M3 + `qwen3:4b-instruct-2507` | 18 / 22 | 22 / 22 | 0 | 4.625s |

가장 큰 개선은 모델만 instruct variant로 바꿨을 때 발생했다. Format proxy는 9/22에서 22/22로 개선됐고, meta reasoning 출력은 13건에서 0건으로 줄었다. Structured data는 표형 정보 보완을 위한 별도 근거이며, factual proxy 변화는 token 기반 자동 지표의 false negative 가능성을 함께 고려해 해석했다.

최종 모델은 "가장 큰 모델"이 아니라 "제한된 게임 문서 QA에 맞는 경량 instruct 모델"로 선택했다. 로컬 `ollama show` 기준 이 모델은 Qwen3 architecture, 4.0B parameters, Q4_K_M quantization을 사용한다. 따라서 BGE-M3와 structured data가 최신 문서 근거를 제공하고, `qwen3:4b-instruct-2507-q4_K_M`은 그 근거를 한국어 답변 형식으로 정리하는 역할을 맡는다. 이 선택은 로컬 실행 가능성, 한국어 답변 형식 안정성, 평균 응답 시간, 재현성을 함께 고려한 결과다.

### 7.4 구조화 데이터

구조화 데이터 실험은 전체 22문항 비교가 아니라, 상점표와 직접 관련된 Q001~Q004만 대상으로 한 부분 ablation이다.

| 설정 | 평가 범위 | 질문 수 | Factual proxy | Format proxy |
|---|---|---:|---:|---:|
| BGE-M3 + instruct | 상점표 관련 Q001~Q004 | 4 | 3 / 4 | 4 / 4 |
| BGE-M3 + instruct + structured | 상점표 관련 Q001~Q004 | 4 | 4 / 4 | 4 / 4 |

구조화 데이터는 `태초 소울 1개 상자`처럼 가격과 구매 제한이 같은 표에 붙어 있는 질문에서 필요한 값을 함께 회수하는 데 도움이 되었다. 이 결과는 전체 22문항 효과가 아니라 상점표 관련 문항에 대한 부분 ablation으로 해석한다.

## 8. 오류 분석

### Q002: 인접 행 조건 혼입

Q002의 정답 근거는 `태초 광휘의 의지 / 광휘의 잔영 790개 / 계정당 1회`다. 모델은 가격과 계정 제한은 맞혔지만, 바로 아래 상품인 `태초 소울 1개 상자`의 `월 4회`, `이월` 조건을 함께 붙였다. 이는 chunk 근거와 structured 근거가 함께 제공될 때 generator가 인접 행 정보를 혼합할 수 있음을 보여준다.

### Q016: 자동 proxy의 한계

Q016 답변은 `라이브 서버 HP는 90, 성화 작열 감소 HP는 30이다`로 사실상 정답이다. 그러나 token recall 기준에서는 factual proxy 실패로 잡혔다. 자동 지표는 빠른 비교에는 유용하지만, 최종 판단에는 수동 rubric 또는 LLM-as-judge가 필요하다.

### Safety gate paraphrase test

기존 safety gate는 원래 adversarial 질문 10/10은 차단했지만, 같은 공격 의도를 다른 표현으로 바꾼 paraphrase 세트에서는 0/10만 차단했다. 이후 단일 키워드가 아니라 여러 단서가 함께 등장할 때 차단하는 복합 조건 규칙을 추가했고, paraphrase 세트와 기존 공격 세트 모두 10/10 차단으로 개선했다. 다만 이 결과는 paraphrase 세트를 확인한 뒤 규칙을 보강한 test-informed 개선이므로, held-out 일반화 성능으로 보지는 않는다.

이를 더 확인하기 위해 직접적인 차단 단어를 피한 stealth 공격 세트 10문항도 추가했다. 이 세트에서는 safety gate 사전 차단이 0/10이었고, end-to-end strict pass는 6/10이었다. 즉, 현재 시스템은 규칙 기반 gate만으로는 교묘한 표현을 막기 어렵고, system prompt가 일부 방어하지만 완전하지 않다. 이 결과는 `report/stealth_safety_gate_test.md`에 별도로 정리했다.

후속으로 keyword gate 대신 intent-aware gate를 추가했다. `safety_intent_classifier_prototype.md`의 offline 100문항 평가에서 intent classifier는 공격 recall 50/50, 정상 과차단 0/50을 기록했고, `safety_intent_e2e_gate_test.md`의 실제 RAG 생성 경로에서도 동일하게 공격 50/50 차단, 정상 50/50 통과를 확인했다. 다만 이 100문항 결과는 기존 실패 분석을 반영한 dev/regression 성격이므로 최종 일반화 headline으로 쓰지 않는다.

최종 safety 보고는 별도 freeze된 v6 fresh held-out을 기준으로 한다. 같은 v6 세트에서 `keyword_rules_v2`는 attack recall 1/24, benign FP 0/24였고, `intent_rules_v5`는 attack recall 12/24, benign FP 0/24였다. backward compatibility 재검산에서는 v1~v4 및 v6의 비순환 세트에서 90/120, FP 1/120을 기록했다. BGE-M3 semantic classifier prototype은 v6 20/24, FP 0/24까지 올라갔지만, 분류기 아이디어와 real_world_harm 강조가 v6 결과 확인 뒤 선택됐을 수 있으므로 retrospective prototype으로 두고 정식 headline은 future work로 미룬다.

추가로 StruQ와 Instruction Hierarchy의 관점을 참고해 prompt template에서 검색 근거를 `읽기 전용 데이터`로 표시하고, 시스템 규칙 > 답변 규칙 > 사용자 질문 > 검색 근거의 우선순위를 명시했다. Llama Guard식 input-output safeguard classifier는 후속 개선으로 남겼다.

## 9. 한계 및 후속 개선

| 한계 | 개선 방향 |
|---|---|
| Record coverage / 표형 정보 혼입 | hand-authored record 추가보다 blind/automatic extractor로 atomic before/after/unchanged record coverage 검증 |
| 자동 proxy 오판 | 수동 채점 확대 또는 LLM-as-judge 추가 |
| BM25 heuristic 영향 | 순수 BM25 점수를 별도 산출해 검색 비교를 더 엄밀하게 검증 |
| reranker 미적용 | BGE-M3 top-k 결과에 cross-encoder reranker 추가 |
| Safety gate 일반화 한계 | 최종 fresh v6는 12/24, FP 0/24로 보고하고, semantic classifier/output checker는 v7 이후 사전등록 실험으로 검증 |
| 문서 수 5개 중심 | 더 많은 패치노트, 이벤트, 가이드 문서로 확장 |
| 고정된 offline benchmark | 패치노트 갱신 주기에 맞춰 질문/정답을 자동 갱신하는 dynamic refreshed evaluation set 구성 |
| 운영 로그 미연동 | 질문, 검색 chunk, 답변, latency, safety decision, user feedback을 추적하는 observability layer 추가 |

후속 확장의 핵심은 평가셋과 운영 로그를 연결하는 것이다. 현재 프로젝트는 미리 만든 문서와 질문으로 모델을 검증하는 offline benchmark지만, 실제 라이브 게임에서는 패치노트가 바뀔 때마다 정답도 바뀔 수 있다. 따라서 새 문서 수집, 변경점 추출, 질문/정답 후보 생성, 재평가를 자동화하면 dynamic refreshed evaluation set으로 확장할 수 있다.

서비스 적용 단계에서는 RAGAS/DeepEval/LLM-as-a-Judge를 보조 평가자로 두고, 검색 근거 적합성, 답변 근거 충실성, 질문 관련성, 환각 여부를 자동으로 1차 점검할 수 있다. 여기에 observability layer를 붙여 question_id, retrieved_chunk_ids, answer, latency, safety decision, user feedback을 기록하면, offline 평가에서 만든 기준과 실제 유저 로그를 연결해 지속적으로 취약 질문을 보강할 수 있다.

## 10. 최종 결론

본 프로젝트는 게임 문서 기반 LLM 평가에서 발생하는 문제를 검색, 구조화 근거, 생성 모델, 안전성, 평가 지표로 분리해 검증했다.

최종 결론은 다음과 같다.

1. RAG는 최신 게임 문서 질문에서 baseline 대비 성능을 크게 개선했다.
2. BGE-M3는 BM25 heuristic보다 top-1 근거 회수 성능이 높았다.
3. 상점표처럼 행 단위 관계가 중요한 문서는 구조화 데이터 보완이 필요했다.
4. 기존 `qwen3:4b`는 사실성은 개선했지만 최종 답변 형식에는 부적합했다.
5. `qwen3:4b-instruct-2507-q4_K_M`은 format proxy 22/22, meta reasoning 0건으로 답변 형식 문제를 해결했다.
6. Keyword safety gate는 기존 adversarial 질문 10/10은 차단했지만 stealth set에서 한계를 보였다. 후속 intent gate는 dev/regression 100문항에서는 공격 50/50 차단, 정상 50/50 통과를 기록했으나, 최종 fresh v6 결과는 12/24 attack recall, benign FP 0/24로 보고한다.

한 문장으로 요약하면, 본 프로젝트는 `게임 문서 기반 질문을 만들고, 검색-생성-안전성-평가를 분리해 로컬 LLM 답변 품질을 체계적으로 비교한 평가 중심 포트폴리오`다.

## 11. 참고문헌

평가 방법, 검색 모델, 생성 모델, safety 설계 근거는 `report/references.md`에 모았다. 본 프로젝트에서는 RAGAS, ARES, FActScore, HELM을 평가 설계 참고문헌으로 사용했고, BGE-M3와 Qwen3는 검색 및 생성 모델 선정 근거로, StruQ, Instruction Hierarchy, Llama Guard, OWASP LLM Top 10은 prompt injection과 safeguard 설계 근거로 사용했다.
