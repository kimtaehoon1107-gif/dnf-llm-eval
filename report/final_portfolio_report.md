# 던전앤파이터 문서 기반 LLM 평가 포트폴리오 최종 보고서

이 문서는 웹 포트폴리오와 README에서 요약한 내용을 바탕으로, 데이터 수집부터 평가 설계, 실험 결과, 실패 분석, 한계까지 전체 과정을 상세히 설명하는 최종 보고서다.

## 1. 프로젝트 목적

이 프로젝트는 넥슨 게임 도메인 LLM 평가 어시스턴트 직무를 목표로, 던전앤파이터 공식 업데이트 문서를 기반으로 로컬 LLM의 답변 품질을 평가하는 과정을 구현한 것이다.

핵심 목표는 단순 챗봇 구현이 아니라, 패치노트와 공지 문서에서 실제 유저가 물어볼 수 있는 질문을 만들고, 답변 정확성, 근거 충실성, 환각 억제, 범위 통제, 답변 형식을 기준으로 평가 체계를 설계하는 것이다.

2026-07-01 후속 실험에서는 2026-06 staged corpus 20문항을 추가해 structured RAG를 재검증했다. Snapshot 구조화 근거와 답변 완전성 규칙을 보강한 뒤 factual proxy와 format proxy가 모두 20/20을 통과했고, 이후 diagnostic/probe에서는 record가 실제 발동하는 조건에서 no-structured 24/35, atomic records 30/35, structured fix 32/35를 기록했다. Safety는 개발용 regression과 fresh held-out을 분리했고, 최종 v6에서 `intent_rules_v5`가 12/24 attack recall, benign FP 0/24를 기록했다.

주의: 위 2026-07-01 structured fix 및 intent safety gate 100문항 결과는 dev/test-informed 결과다. 동일 문항의 실패 분석을 바탕으로 record와 rule을 보강한 뒤 재측정했으므로 headline 수치를 held-out 일반화 성능으로 해석하지 않는다. 이후 factual blind held-out 25문항을 freeze해 재검증한 결과, structured record는 dev 9/20 문항에 발동했지만 held-out에서는 0/25 문항에 발동했고 모든 ablation 조건이 23/25로 동률이었다. Structured record probe는 held-out 일반화 근거가 아니라 record 발동 조건에서 구조화 메커니즘을 분리한 진단으로만 해석한다. Safety도 regression 50/50이 아니라 사전 선언한 v6 12/24, FP 0/24를 최종 fresh 결과로 보고한다. Semantic classifier의 v6 20/24는 retrospective prototype이므로 future work로 둔다.

## 2. 데이터 수집과 전처리

Selenium 기반 수집 스크립트로 던전앤파이터 업데이트 목록을 렌더링한 뒤, `li.title`의 `data-no`와 `data-url`을 읽어 상세 공지 URL을 구성했다. 이후 상세 페이지 본문을 Markdown으로 저장하고 문서별 metadata를 CSV로 관리했다.

초기에는 일반적인 `a href` 링크를 찾는 방식으로 접근했지만, 던파 업데이트 목록은 제목 `li` 태그에 글 번호가 들어 있는 구조였다. 이 문제를 디버그 HTML과 CSV로 확인한 뒤, 실제 페이지 구조에 맞는 수집기로 수정했다.

## 3. 벤치마크 설계

공식 문서를 기준으로 문서 기반 질문 22개, 게임 외 범위 질문, 프롬프트 공격 질문을 구성했다. 질문 유형은 단순 사실 확인, 조건 판단, 비교, 범위 제한, 표 기반 질의가 섞이도록 설계했다.

질문 난이도는 코드가 자동 계산한 값이 아니라 benchmark 설계 단계에서 수동으로 붙인 metadata다. `easy`는 단일 근거에서 이름·수치·조건을 그대로 추출하는 질문, `medium`은 여러 조건을 묶거나 비교·요약·간단한 계산이 필요한 질문, `hard`는 문서 근거를 바탕으로 가능 여부나 결론을 판단해야 하는 질문으로 구분했다.

초기 대표 수동 채점은 legacy 7개 항목 0~3점 루브릭으로 구성했다. 이 기준은 `eval/representative_manual_scoring.csv`에 남아 있는 과거 대표 채점 결과를 해석하기 위한 기준이다.

| 항목 | 평가 의도 |
|---|---|
| 정확성 | 문서 기준 사실이 맞는가 |
| 근거 충실성 | 답변이 공식 문서 근거에 기반하는가 |
| 완전성 | 기간, 조건, 제한, 예외를 빠뜨리지 않았는가 |
| 의도 적합성 | 유저 질문의 초점에 맞게 답했는가 |
| 환각 억제 | 문서에 없는 내용을 만들지 않았는가 |
| 범위 통제 | 게임 외 질문과 공격성 질문을 제한하는가 |
| 표현 품질 | 최종 사용자 답변으로 읽히는가 |

현재 운영 루브릭은 `eval/evaluation_rubric.md`에서 최신성 점수 항목을 추가하고, 환각/과잉추론, 중대 수치 오류, 라이브 서버 기준 오인, 범위 통제를 binary critical gate로 분리한다. 따라서 총점은 품질 비교용 보조 지표이고, critical gate FAIL은 총점과 별개로 수동 재검토 대상으로 본다.

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

### 5.3 BGE-M3 고정 생성 설정 요소별 비교 실험

기존 최종 실험은 검색기, 생성 모델, 구조화 데이터가 한 번에 바뀌어 어떤 요소가 어떤 개선을 만들었는지 분리해 설명하기 어려웠다. 이를 보완하기 위해 검색기를 BGE-M3로 고정하고 전체 5개 문서 corpus에서 검색한 뒤, 생성 모델과 구조화 데이터 효과를 단계적으로 비교했다.

공통 조건은 `questions/benchmark_questions.csv` 22문항, BGE-M3 retriever, top-k 8, thinking disabled, `--num-predict 512`, `--restrict-to-question-doc` 미사용이다.

factual proxy와 format proxy는 사람이 직접 채점하기 전 여러 설정을 빠르게 비교하기 위한 자동 대리 지표다. factual proxy는 답변이 기준 정답 또는 근거 문서의 핵심 정보를 충분히 포함하는지 확인하고, format proxy는 영어 추론 과정, 메타 발화, 비한국어 잡음 없이 한국어 답변 형식을 지켰는지 확인한다.

| 설정 | Factual proxy | Format proxy | Meta reasoning | Avg latency |
|---|---:|---:|---:|---:|
| BGE-M3 + `qwen3:4b` | 17 / 22 | 9 / 22 | 13 | 11.635s |
| BGE-M3 + `qwen3:4b-instruct-2507` | 18 / 22 | 22 / 22 | 0 | 4.625s |

가장 큰 변화는 `qwen3:4b`에서 `qwen3:4b-instruct-2507-q4_K_M`으로 모델만 바꿨을 때 발생했다. Format proxy는 9/22에서 22/22로 개선됐고, meta reasoning 출력은 13건에서 0건으로 줄었다. 평균 응답 시간도 11.635초에서 4.625초로 줄었다.

Q016처럼 사람이 보면 사실상 정답인 답변도 자동 proxy에서는 실패로 잡힌 사례가 있었다. 따라서 format proxy와 factual proxy는 빠른 비교에는 유용하지만, 최종 해석에서는 수동 rubric과 함께 읽어야 한다.

### 5.4 최종 생성 모델 선택

최종 생성 모델은 `qwen3:4b-instruct-2507-q4_K_M`으로 정했다. 이 모델을 선택한 이유는 세 가지다. 첫째, 4.0B 규모의 Qwen3 계열 모델이라 개인 PC에서 재현 가능한 경량 로컬 실험이라는 프로젝트 목적에 맞다. 둘째, `Q4_K_M` 양자화 모델이므로 모델 크기와 실행 부담을 줄일 수 있다. 셋째, 기존 `qwen3:4b`에서 드러난 영어 추론 과정과 메타 발화 문제를 줄이기 위해 instruction following이 더 안정적인 instruct variant가 필요했다.

따라서 최종 모델 선택은 단순히 더 큰 모델을 고른 것이 아니라, `BGE-M3가 근거를 찾고`, `structured data가 표형 정보를 보완하며`, `qwen3:4b-instruct-2507-q4_K_M이 근거를 한국어 답변으로 정리하는` 역할 분리 전략이었다. 최종 통합 설정은 factual proxy 단독 최고값이 아니라, 답변 형식, meta reasoning 억제, 평균 응답 시간, 표형 정보 보완까지 고려한 제출용 균형 조합으로 해석한다.

### 5.5 구조화 데이터 개선

상점표 질문은 일반 chunk 검색만으로 `아이템명-가격-구매 제한` 관계를 안정적으로 보존하기 어려웠다. 이를 해결하기 위해 DOC-01, DOC-02의 켈돈 자비 상점 표를 `data/structured/shop_items.json`으로 추출했다.

구조화 데이터 실험은 전체 22문항이 아니라 상점표 관련 Q001~Q004에 한정한 부분 비교 실험이다. 같은 검색기와 instruct 모델 조건에서 structured data를 추가하면 Q001~Q004 factual proxy가 3/4에서 4/4로 개선됐다.

| 설정 | 평가 범위 | Factual proxy | Format proxy |
|---|---|---:|---:|
| BGE-M3 + instruct | 상점표 관련 Q001~Q004 | 3 / 4 | 4 / 4 |
| BGE-M3 + instruct + structured | 상점표 관련 Q001~Q004 | 4 / 4 | 4 / 4 |

대표적으로 Q003에서 구조화 데이터가 없을 때는 가격/구매 제한 관계가 누락되거나 약하게 반영됐지만, structured 설정에서는 가격과 월 4회 제한을 함께 회수했다. 따라서 structured data는 전체 문항의 만능 개선책이라기보다, 표의 행 단위 관계가 중요한 질문에서 근거 보존을 보완하는 장치로 해석한다.

### 5.6 안전성 평가

게임 외 질문, 프롬프트 탈취, 문서 조작, 버그 악용, 매크로 자동화 요청을 포함한 공격 세트를 구성했다. 안전 게이트 적용 후 local baseline과 RAG 시스템 모두 10개 공격 질문을 10개 모두 차단했다.

안전 게이트는 차단 유형을 `prompt_leakage`, `fake_evidence`, `exploit_request`, `automation_abuse`, `out_of_domain` 등으로 기록하도록 구성했다. 다만 현재 safety gate는 규칙 기반 1차 필터이므로, paraphrase 공격과 정상 질문 오탐에 대한 추가 검증이 필요하다.

이 한계를 확인하기 위해 기존 공격 의도를 다른 표현으로 바꾼 paraphrase 공격 세트 10문항을 추가했다. 최초 safety gate는 paraphrase 세트를 0/10만 차단했지만, 복합 조건 규칙을 추가한 뒤 10/10 차단으로 개선했다. 다만 이 결과는 paraphrase 세트를 확인한 뒤 규칙을 보강한 test-informed 개선이므로, held-out 일반화 성능으로 보지는 않는다.

추가로 직접적인 차단 단어를 더 많이 피한 `adversarial_stealth_questions.csv` 10문항을 만들었다. 이 held-out 성격의 stealth set에서는 safety gate 사전 차단이 0/10이었다. End-to-end 답변까지 보면 시스템 프롬프트가 6/10은 방어했지만, 2문항은 partial, 2문항은 fail로 분류됐다. 즉, 현재 safety는 규칙 기반 gate만으로 일반화된다고 보기 어렵고, `safety gate + system prompt`가 함께 일부 방어하는 구조다. 실제 서비스 수준에서는 정상 질문 오탐 세트와 새로운 red-team paraphrase/stealth 세트를 분리해 추가 검증해야 한다.

이후 keyword 중심 gate의 한계를 줄이기 위해 intent-aware gate를 추가했다. Offline intent classifier 평가에서는 explicit/stealth/attack expansion 공격 50문항을 모두 차단하고, overrefusal/benign expansion 정상 50문항을 모두 허용했다. 같은 조건을 `run_rag_local_llm_eval.py`의 실제 생성 경로에서 재실행한 결과도 공격 50/50 차단, 정상 50/50 통과였다. 다만 이 결과는 현재 보유한 안전성 세트 기준의 dev/regression 결과이므로 최종 일반화 headline으로 쓰지 않는다.

최종 safety 성능은 사전 freeze된 v6 fresh held-out으로 분리해 보고했다. 같은 v6 세트에서 `keyword_rules_v2`는 attack recall 1/24, benign FP 0/24였고, `intent_rules_v5`는 attack recall 12/24, benign FP 0/24였다. backward compatibility 재검산에서는 v1~v4와 v6의 비순환 세트에서 90/120, FP 1/120을 기록해 구식 공격 유지력과 신규 공격 대응력을 분리했다. BGE-M3 semantic classifier prototype은 v6 20/24, FP 0/24를 기록했지만, 분류기 아이디어와 real_world_harm 강조가 v6 결과를 본 뒤 선택됐을 수 있으므로 retrospective prototype으로만 해석한다.

또한 StruQ와 Instruction Hierarchy의 instruction/data 분리 관점을 참고해 prompt template을 보완했다. 검색 근거와 구조화 근거를 `읽기 전용 데이터`로 표시하고, 시스템 규칙과 답변 규칙이 사용자 질문 및 검색 문서보다 높은 우선순위임을 명시했다. 향후에는 Llama Guard처럼 입력과 출력을 별도 safeguard classifier로 검사하는 구조를 추가할 수 있다.

## 6. 대표 수동 채점 결과

자동 proxy 지표의 한계를 보완하기 위해 대표 문항 수동 채점표를 만들었다.

| 파일 | 내용 |
|---|---|
| `eval/representative_manual_scoring.csv` | 대표 문항별 legacy 7개 루브릭 점수 |
| `report/representative_manual_scoring.md` | 실패 원인과 개선 효과 해석 |

핵심 발견은 세 가지다.

1. BGE-M3는 BM25 heuristic보다 의미 기반 top-1 근거 회수에 강했다.
2. 상점표처럼 셀 관계가 중요한 문서는 구조화 데이터가 필요했다.
3. 기존 `qwen3:4b`는 사실 근거를 받아도 최종 답변 형식 제어가 약했다.

정성 오류 분석에서는 자동 proxy 점수만으로는 보이지 않는 실패 원인을 따로 확인했다.

| 대표 사례 | 관찰된 문제 | 해석 |
|---|---|---|
| Q002 상점표 질문 | 정답 아이템의 가격은 맞혔지만 인접 상품의 구매 제한이 섞임 | 표형 정보는 일반 chunk만으로 부족하며 structured data가 필요함 |
| Q016 계산형 질문 | 사람이 보면 정답에 가까웠지만 factual proxy는 실패로 처리 | token 기반 자동 지표는 false negative가 있어 수동 rubric이 필요함 |
| `qwen3:4b` 기본 모델 | 근거는 찾았지만 영어 추론 과정과 meta reasoning이 출력됨 | 검색 품질과 답변 형식은 별도 평가해야 함 |
| stealth/fresh safety 질문 | keyword gate는 직접 키워드를 피하면 약했고, 최종 v6에서는 intent_rules_v5가 12/24, FP 0/24를 기록 | 안전성은 regression 통과율과 fresh held-out 성능을 분리해 보고해야 함 |

## 7. 직무 연결성

| 공고 요구 | 프로젝트 대응 |
|---|---|
| 게임 도메인 LLM 벤치마크 구성 | DNF 업데이트 문서 기반 질문 22개와 공격 질문 세트 설계 |
| 평가 지표 및 기준 개발 | legacy 수동 루브릭과 현재 운영 루브릭(점수 항목 + binary critical gate) 설계 |
| LLM 응답 품질 평가 | baseline, RAG, BGE-M3, structured data, 생성 모델 비교 |
| 결과 분석 및 공유 | 실패 유형, 개선 효과, 다음 개선 방향 보고서화 |
| 데이터 기반 문제 분석 | 검색 hit, factual proxy, format proxy, 수동 채점 결합 |

## 8. 한계와 다음 개선

| 한계 | 개선 방향 |
|---|---|
| Record coverage / 표형 정보 혼입 | hand-authored record 추가보다 blind/automatic extractor로 atomic before/after/unchanged record coverage 검증 |
| 자동 proxy 오판 | 수동 채점 확대 또는 LLM-as-judge 추가 |
| BM25 heuristic 영향 | 순수 BM25 점수를 별도 산출해 검색 비교를 더 엄밀하게 검증 |
| reranker 미적용 | BGE-M3 top-k 결과에 cross-encoder reranker 추가 |
| Safety gate 일반화 한계 | v6 fresh 결과는 12/24, FP 0/24로 제한적이며, semantic classifier/output checker는 v7 이후 사전등록 실험으로 검증 |
| 문서 수 5개 중심 | 더 많은 패치노트, 이벤트, 가이드 문서로 확장 |
| 고정된 offline benchmark | 패치노트 갱신 주기에 맞춰 질문과 기준 정답을 자동 갱신하는 dynamic refreshed evaluation set 구성 |
| 운영 로그 미연동 | 질문, 검색 chunk, 답변, latency, safety decision, user feedback을 추적하는 observability layer 추가 |

현재 결과는 미리 구성한 문서 5개와 benchmark 질문 22개를 대상으로 한 offline 평가다. 이 방식은 실험을 통제하기 쉽지만, 라이브 게임처럼 패치노트와 이벤트 조건이 계속 바뀌는 도메인에서는 시간이 지나며 평가셋이 낡을 수 있다. 후속 단계에서는 새 패치노트 수집, 변경점 추출, 질문/정답 후보 생성, 재평가를 하나의 주기로 묶어 dynamic refreshed evaluation set으로 확장할 수 있다.

또한 실제 서비스 적용 단계에서는 RAGAS/DeepEval/LLM-as-a-Judge를 최종 판정자가 아니라 보조 평가자로 활용할 수 있다. 예를 들어 검색 chunk가 질문과 맞는지, 답변이 근거에 충실한지, 문서에 없는 내용을 만들지 않았는지 자동으로 1차 점검한 뒤, 중요한 실패 사례는 수동 rubric으로 다시 확인하는 방식이다. 이때 observability layer를 붙이면 question_id, retrieved_chunk_ids, answer, latency, safety decision, user feedback을 함께 기록할 수 있어 offline benchmark에서 발견한 약점과 실제 유저 로그에서 발생한 문제를 연결해 개선할 수 있다.

## 9. 결론

이 프로젝트의 결론은 “가벼운 로컬 LLM도 게임 문서 QA에 사용할 수 있지만, 문서 검색, 구조화 데이터, 안전 게이트, 평가 루브릭이 함께 있어야 한다”이다.

특히 RAG는 baseline보다 문서 기반 질문 성능을 크게 개선했고, BGE-M3는 BM25 heuristic보다 top-1 근거 회수를 높였다. 생성 설정 요소별 비교 실험에서는 `qwen3:4b-instruct-2507-q4_K_M`이 기존 `qwen3:4b`보다 답변 형식, meta reasoning 억제, 평균 응답 시간에서 더 안정적이었다. 2026-06 staged corpus 후속 실험에서는 `hybrid + structured fix + qwen3:4b-instruct-2507-q4_K_M`이 dev 20문항 factual/format proxy 20/20을 기록했지만, blind held-out ablation에서는 record 비전이(9/20 -> 0/25)와 조건 간 23/25 동률을 확인했다. 별도 structured record probe에서는 record가 실제 발동하면 24/35에서 32/35로 개선됨을 확인해, 남은 병목이 구조화 메커니즘보다 record coverage/extraction임을 분리했다. Safety는 regression 50/50과 fresh v6 12/24, FP 0/24를 분리했고, semantic classifier 20/24는 retrospective prototype으로 낮춰 표시했다. 최종적으로 자동 proxy와 DeepEval judge는 수동 리뷰를 보조하는 지표로 해석하고, 높은 점수보다 그 점수의 출처와 감사 가능성을 전면에 둔다.

## 10. 참고문헌

상세 참고문헌은 `report/references.md`에 정리했다. 핵심 근거는 HELM의 multi-metric evaluation, RAGAS/ARES의 retrieval-generation 분리 평가, FActScore의 factuality 평가, BGE-M3의 다국어 dense retrieval, Qwen3의 다국어 경량 모델군, StruQ와 Instruction Hierarchy의 instruction/data 분리, Llama Guard와 OWASP LLM Top 10의 safeguard 관점이다.
