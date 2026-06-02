# 모델 선택 및 벤치마크 설계 근거

작성일: 2026-05-28

## 1. 왜 LLM 평가 벤치마크를 만들었는가

지원 직무의 핵심 업무는 게임 도메인 문서를 기반으로 LLM 성능을 검증하고, 평가 기준과 스코어링 방식을 설계하며, 결과를 분석해 모델 개선 인사이트를 전달하는 것이다.

따라서 본 프로젝트는 단순히 게임 문서를 요약하는 챗봇이 아니라, 다음 항목을 직접 보여주는 평가 벤치마크로 설계했다.

- 게임 업데이트 문서 기반 질문 설계
- 기준 정답과 원문 근거 작성
- 문서 기반 답변의 정확성/근거성 평가
- 게임 외 질문에 대한 범위 통제 평가
- baseline과 RAG 방식의 성능 비교
- 오류 유형 분석과 개선 방향 도출

## 2. 왜 던파 업데이트 문서를 사용했는가

던전앤파이터 업데이트 문서는 LLM 평가 데이터로 적합하다.

이유는 다음과 같다.

- 실제 게임 유저가 궁금해할 만한 정보가 많다.
- 명성, 피로도, 구매 가격, 제한 횟수, 초기화 시간처럼 수치형 정보가 많다.
- 계정당, 월 단위, 주간 단위, 특정 NPC, 특정 콘텐츠처럼 조건 정보가 많다.
- 퍼스트 서버/라이브 서버처럼 문서 버전과 맥락 구분이 중요하다.
- 문서 밖 추측이나 오래된 게임 지식이 섞이면 유저에게 잘못된 안내가 될 수 있다.

따라서 게임 도메인 LLM 평가에서 중요한 정확성, 근거성, 완전성, 환각 방지, 범위 통제를 모두 확인하기 좋다.

## 3. 평가척도 설계 근거

본 프로젝트의 평가척도는 다음 연구 흐름을 참고했다.

### HELM

HELM은 언어모델을 단일 정확도만으로 평가하지 않고, 시나리오와 여러 평가 지표를 함께 고려하는 multi-metric 평가를 제안한다. HELM은 accuracy뿐 아니라 calibration, robustness, fairness, bias, toxicity, efficiency 등 여러 지표를 함께 측정해 모델의 trade-off를 드러내는 접근을 강조한다.

본 프로젝트 적용:

- 단순 정답 여부만 보지 않고 7개 항목으로 평가했다.
- 정확성, 근거성, 완전성, 환각 방지, 범위 통제, 표현 품질을 분리했다.
- 질문 유형별, 문서별 실패 유형을 따로 분석했다.

출처: https://arxiv.org/abs/2211.09110

### RAGAS

RAGAS는 RAG 시스템 평가에서 retrieval이 적절한 문맥을 찾았는지, LLM이 그 문맥을 충실히 활용했는지, 생성 답변 자체가 질문에 맞는지 나눠 봐야 한다고 설명한다.

본 프로젝트 적용:

- RAG 검색 결과 chunk를 CSV에 저장해 어떤 근거가 제공됐는지 추적했다.
- `근거성` 항목으로 답변이 검색된 근거에 의해 뒷받침되는지 평가했다.
- `사용자 의도 적합성` 항목으로 답변이 질문 초점에 맞는지 평가했다.

출처: https://arxiv.org/abs/2309.15217

### ARES

ARES는 RAG 평가 차원을 context relevance, answer faithfulness, answer relevance로 나누고, 자동 평가와 인간 주석을 결합하는 접근을 제안한다.

본 프로젝트 적용:

- context relevance: 검색된 chunk가 질문에 적절한지 dry-run 파일로 확인했다.
- answer faithfulness: 답변이 근거와 충돌하지 않는지 평가했다.
- answer relevance: 답변이 질문에 직접 답하는지 평가했다.
- 작은 개인 프로젝트이므로 완전 자동 평가 대신 기준 정답과 수동 채점 메모를 남겼다.

출처: https://arxiv.org/abs/2311.09476

### FActScore

FActScore는 긴 답변을 원자적 사실 단위로 나누고, 각 사실이 지식 출처에 의해 뒷받침되는지 평가하는 관점을 제시한다.

본 프로젝트 적용:

- 답변 안의 수치, 아이템명, NPC명, 제한 횟수, 초기화 시점을 개별 사실로 보았다.
- 답변이 대체로 맞아도 핵심 수치 하나가 틀리면 정확성에서 감점했다.
- 문서 근거가 없는 고유명사나 조건을 말하면 환각으로 기록했다.

출처: https://arxiv.org/abs/2305.14251

## 4. 최종 평가척도

| 평가척도 | 정의 | 도입 이유 |
|---|---|---|
| 정확성 | 원문과 답변의 사실 일치도 | 게임 업데이트는 수치/조건 오류가 치명적이다 |
| 근거성 | 답변이 제공 문서 evidence로 뒷받침되는 정도 | 문서 기반 QA의 핵심은 출처 기반 답변이다 |
| 완전성 | 필요한 조건과 예외를 빠짐없이 포함하는 정도 | 일부 조건 누락은 유저 오해를 만든다 |
| 사용자 의도 적합성 | 질문 의도에 직접 답하는 정도 | 장황하거나 엉뚱한 답변을 방지한다 |
| 환각 방지 | 문서에 없는 사실을 추가하지 않는 정도 | 게임 외 지식/추측 생성을 막는다 |
| 범위 통제 | 문서 범위 밖 질문을 거절하는 정도 | 도메인 제한형 QA 어시스턴트의 안전장치다 |
| 표현 품질 | 유저가 이해하기 쉬운 한국어 답변인지 | 실제 서비스 응답 품질과 연결된다 |

## 5. 왜 qwen3:4b를 사용했는가

본 프로젝트는 ChatGPT 같은 대형 상용 모델을 대체하려는 것이 아니라, 제한된 게임 문서 QA에서 경량 로컬 LLM의 가능성과 한계를 평가하는 것이 목적이다.

qwen3:4b를 선택한 이유는 다음과 같다.

1. 로컬 실행 가능한 크기
   - Ollama의 qwen3:4b 페이지 기준 모델 크기는 약 2.5GB이며, 4.02B 파라미터의 Q4_K_M 양자화 모델이다.
   - 개인 PC에서 실험 가능한 크기이므로 “자원 제약 환경에서의 평가”라는 프로젝트 목적에 맞다.
   - 출처: https://ollama.com/library/qwen3:4b

2. 한국어 문서 실험에 유리한 다국어 모델군
   - Qwen3 Technical Report는 Qwen3가 성능, 효율성, 다국어 능력을 목표로 한 모델군이며 0.6B부터 235B까지 다양한 크기를 제공한다고 설명한다.
   - 또한 Qwen3는 119개 언어/방언 지원을 언급하므로 한국어 게임 문서 실험 후보로 적합하다고 판단했다.
   - 출처: https://arxiv.org/abs/2505.09388

3. Ollama에서 쉽게 재현 가능
   - Ollama 공식 문서와 모델 라이브러리는 `ollama run qwen3:4b` 방식으로 로컬 실행할 수 있음을 제공한다.
   - GitHub에 코드를 공개했을 때 다른 사람도 같은 모델명으로 실험을 재현하기 쉽다.
   - 출처: https://ollama.com/library/qwen3:4b

4. 너무 큰 모델을 쓰지 않는 실험 설계
   - 본 프로젝트의 목적은 최고 성능 모델을 찾는 것이 아니라, 경량 모델이 문서 제공 방식에 따라 얼마나 개선되는지 보는 것이다.
   - qwen3:4b는 baseline에서 실패가 드러날 만큼 충분히 가볍고, RAG 적용 후 개선을 확인할 만큼 기본 성능이 있는 모델이었다.

## 5.1 왜 qwen3:4b-instruct-2507-q4_K_M을 최종 생성 모델로 선택했는가

초기 실험의 기준 모델은 `qwen3:4b`였지만, 최종 제출용 생성 모델은 `qwen3:4b-instruct-2507-q4_K_M`으로 바꿨다. 이유는 단순히 새 모델이라서가 아니라, 게임 서비스 답변에는 사실성뿐 아니라 출력 형식, 한국어 안내체, 평균 응답 시간, 로컬 재현성이 함께 필요하기 때문이다.

비교 실험에서는 검색기를 BGE-M3로 고정하고, 생성 모델과 프롬프트/구조화 데이터만 단계적으로 바꿨다.

| 설정 | Factual proxy | Format proxy | Meta reasoning | Avg latency |
|---|---:|---:|---:|---:|
| BGE-M3 + `qwen3:4b` | 17 / 22 | 9 / 22 | 13 | 11.635s |
| BGE-M3 + `qwen3:4b-instruct-2507` | 18 / 22 | 22 / 22 | 0 | 4.625s |
| BGE-M3 + instruct + service-tone | 16 / 22 | 22 / 22 | 0 | 4.989s |
| BGE-M3 + instruct + service-tone + structured | 17 / 22 | 22 / 22 | 0 | 5.130s |

이 결과에서 가장 큰 변화는 모델만 instruct variant로 바꿨을 때 발생했다. Format proxy는 9/22에서 22/22로 개선됐고, meta reasoning 출력은 13건에서 0건으로 줄었으며, 평균 응답 시간도 줄었다. 따라서 최종 모델 선택의 핵심 근거는 “더 큰 모델”이 아니라 “제한된 게임 문서 QA에서 로컬 실행 가능하고, 서비스 답변 형식을 안정적으로 따르는 경량 instruct 모델”이라는 점이다.

또한 `Q4_K_M` 양자화 모델을 사용한 이유는 개인 PC에서 재현 가능한 실험 환경을 유지하기 위해서다. 실제 서비스 관점에서도 모델 크기와 VRAM 비용, latency는 중요한 제약이다. 본 프로젝트는 대형 API 모델의 최대 성능을 보여주는 것이 아니라, 공식 문서 RAG와 평가 루브릭을 결합했을 때 경량 로컬 모델이 어디까지 안정적으로 동작하는지 검증하는 데 초점을 두었다.

## 6. 왜 Llama 3.2를 주 모델로 쓰지 않았는가

Llama 3.2 1B/3B도 로컬 실행 대안으로 검토했다. Ollama의 Llama 3.2 페이지는 1B와 3B 크기를 제공하며, 로컬 실행과 요약/검색 작업 등에 활용 가능하다고 설명한다.

다만 본 프로젝트의 주 데이터는 한국어 게임 문서다. Ollama의 Llama 3.2 페이지에서 공식 지원 언어로 제시된 목록에는 한국어가 포함되어 있지 않다. 그래서 주 모델은 qwen3:4b로 선택하고, Llama 3.2는 PC 자원이 부족할 때의 대안 또는 비교군으로 남겼다.

출처: https://ollama.com/library/llama3.2

## 7. 왜 baseline과 RAG를 비교했는가

처음부터 RAG만 사용하면 개선 효과를 설명하기 어렵다. 따라서 먼저 baseline을 만들었다.

Baseline:

```text
질문 → 연결된 doc_id의 문서 전체 입력 → qwen3:4b 답변 → 채점
```

RAG:

```text
질문 → 문서 chunk 검색 → 관련 근거 chunk 입력 → qwen3:4b 답변 → 채점
```

비교 결과:

| 방식 | 문서 기반 질문 평균 |
|---|---:|
| Baseline | 11.27 / 21 |
| RAG | 18.86 / 21 |

이 비교를 통해 “경량 모델의 성능은 모델 자체뿐 아니라 근거 제공 방식에 크게 좌우된다”는 분석을 도출했다.

## 8. 현재 RAG 검색 방식: BM25 heuristic

현재 구현된 RAG baseline은 순수 BM25가 아니라 BM25 점수에 phrase/coverage/intent bonus를 더한 BM25 기반 heuristic 검색이다.

구성:

```text
질문
→ Markdown 문서 line-window chunk 분할
→ 한국어/영문/숫자 토큰 및 한글 n-gram 토큰화
→ BM25 점수 + phrase/coverage/intent bonus
→ 관련 chunk를 qwen3:4b에 제공
```

BM25를 먼저 사용한 이유는 다음과 같다.

- 구현이 단순하고 재현성이 높다.
- `브레이커`, `명성`, `퍼스트서버`, `광휘의 잔영`처럼 게임 고유명사와 수치 키워드가 많은 문서에 강하다.
- embedding 모델 다운로드 없이 로컬에서 바로 검증할 수 있다.
- baseline 대비 RAG 개선 효과를 빠르게 확인할 수 있다.

다만 이 baseline은 평가 문항의 의도와 가까운 키워드 보너스를 포함하므로, 엄밀한 검색 모델 비교에서는 순수 BM25 점수를 추가로 산출할 필요가 있다. 본 프로젝트에서는 BM25 heuristic을 실무형 키워드 baseline으로 두고 BGE-M3와 비교했다.

다만 BM25는 표현이 다른 의미 유사 질문에는 약할 수 있다. 예를 들어 유저가 “복귀 유저인데 이번 보상 뭐 챙겨야 해?”처럼 문서 표현과 다른 말로 질문하면, 키워드 기반 검색만으로는 관련 이벤트/보상 섹션을 놓칠 수 있다. 따라서 embedding retrieval을 선택형 retriever로 추가했다.

## 9. 선택형 검색 모델: BGE-M3

BGE-M3를 embedding retrieval 후보로 선정하고, `--retriever bge-m3` 옵션으로 실행할 수 있게 구현했다.

선정 이유:

1. 한국어 포함 다국어 검색에 적합
   - BGE-M3 논문은 100개 이상의 언어를 지원하는 다국어 embedding 모델로 설명한다.
   - 던파 업데이트 문서는 한국어 중심이므로 다국어 검색 성능이 중요하다.
   - 출처: https://arxiv.org/abs/2402.03216

2. 긴 문서 검색에 적합
   - BGE-M3는 짧은 문장부터 최대 8192 토큰의 긴 문서까지 처리할 수 있다고 보고한다.
   - 패치노트, 이벤트 공지, 가이드는 한 문서 안에 여러 섹션이 섞여 있어 긴 문서 검색 대응이 중요하다.

3. dense/sparse/multi-vector 검색을 함께 지원
   - 논문은 BGE-M3가 dense retrieval, sparse retrieval, multi-vector retrieval을 동시에 수행할 수 있다고 설명한다.
   - 던파 문서에는 `브레이커`, `태초 소울`, `계정당 월 4회` 같은 정확 키워드와 “복귀 유저 보상”처럼 의미 기반 검색이 모두 필요하다.

적용 계획:

| 비교군 | 목적 |
|---|---|
| BM25 heuristic RAG | 기본 구현, 키워드 중심 검색 baseline |
| BGE-M3 dense RAG | 의미 기반 검색이 문서 탐색을 개선하는지 확인 |

주의할 점:

- 기본 실행은 BM25이며, BGE-M3는 optional dependency 설치 후 사용할 수 있다.
- 첫 실행 시 Hugging Face에서 모델을 다운로드하고 chunk embedding cache를 생성하므로 시간이 오래 걸릴 수 있다.
- 최종 제출용 비교에서는 BM25를 baseline으로, BGE-M3를 최종 검색 후보로 두었다.

22개 benchmark 질문에 대한 retrieval dry-run 비교 결과는 다음과 같다.

| retriever | top-8 evidence hit | top-1 evidence hit | avg token recall |
|---|---:|---:|---:|
| BM25 heuristic | 22 / 22 | 19 / 22 | 0.994 |
| BGE-M3 | 22 / 22 | 21 / 22 | 1.000 |

이 결과는 BGE-M3가 top-1 ranking 기준으로 BM25 heuristic보다 안정적일 수 있음을 보여준다. 두 방식 모두 top-8 안에는 evidence를 포함했으므로, 최종 차이는 실제 답변 생성과 루브릭 채점으로 확인해야 한다.

초기 검색기별 답변 생성 pre-check 결과는 다음과 같다. 이 실험은 검색기 비교 목적의 중간 산출물이며, 최종 생성 설정 ablation은 뒤의 10장에서 별도로 다룬다.

| retriever | factual proxy pass | format proxy pass |
|---|---:|---:|
| BM25 heuristic | 17 / 22 | 0 / 22 |
| BGE-M3 | 19 / 22 | 0 / 22 |

BGE-M3는 factual proxy에서도 BM25 heuristic보다 높았지만, 두 방식 모두 format proxy가 낮았다. 이는 검색 모델을 개선해도 `qwen3:4b`의 영어 추론 과정 노출과 메타 발화 문제가 남는다는 뜻이다. 따라서 다음 개선은 retriever보다 답변 생성 모델의 instruction following 또는 출력 후처리 쪽에 우선순위를 둔다.

## 10. 최종 생성 모델 선택: qwen3:4b-instruct-2507-q4_K_M

초기 답변 생성 모델은 `qwen3:4b`였다. 이 선택은 개인 PC에서 재현 가능한 경량 MVP에 맞춘 것이었다. 그러나 BGE-M3로 검색 품질을 개선한 뒤에도 `qwen3:4b`는 영어식 추론 과정과 메타 발화를 자주 출력했다. 즉, 병목이 retrieval에서 generation format으로 이동했다.

따라서 최종 실험에서는 생성 모델을 `qwen3:4b-instruct-2507-q4_K_M`으로 교체했다.

로컬 `ollama show qwen3:4b-instruct-2507-q4_K_M` 기준 모델 특성은 다음과 같다.

| 항목 | 값 |
|---|---|
| architecture | qwen3 |
| parameters | 4.0B |
| context length | 262144 |
| embedding length | 2560 |
| quantization | Q4_K_M |
| license | Apache License 2.0 |

선택 이유는 다음과 같다.

1. 경량 로컬 실행 조건 유지
   - 4.0B 규모의 Qwen3 계열 모델이므로 개인 PC 기반 실험에 적합하다.
   - `Q4_K_M`은 4bit 계열 양자화 포맷으로, 모델 크기와 실행 부담을 줄이면서도 답변 품질을 비교적 유지하는 선택이다.
   - 본 프로젝트의 목적은 대형 API 모델 성능을 과시하는 것이 아니라, 제한된 자원에서 게임 문서 기반 QA 평가 파이프라인을 설계하는 것이다.

2. Instruct 계열 모델을 통한 형식 제어 개선
   - 기존 `qwen3:4b`는 검색 근거가 좋아져도 "Okay, let's..." 같은 영어 추론 과정이나 메타 발화를 출력했다.
   - 서비스 QA에서는 사실성뿐 아니라 유저에게 바로 보여줄 수 있는 한국어 답변 형식이 중요하다.
   - 그래서 instruction following이 더 안정적인 instruct variant를 선택했다.

3. RAG 구조와 역할 분리가 명확함
   - 최신 던파 지식은 모델 내부 지식이 아니라 BGE-M3 검색과 structured data로 제공한다.
   - 생성 모델은 문서를 새로 "알고 있는" 역할이 아니라, 검색된 근거를 한국어 서비스 답변으로 정리하는 역할을 맡는다.
   - 따라서 4B급 경량 instruct 모델도 제한된 도메인에서는 실험 가치가 있다.

4. 실험 결과에서 형식 품질 개선 확인
   - 최신 ablation에서는 검색기를 BGE-M3로 고정하고 전체 문서 corpus에서 검색했다.
   - `BGE-M3 + qwen3:4b`는 factual proxy 17/22, format proxy 9/22, meta reasoning 13건, 평균 응답 시간 11.635초였다.
   - 모델만 `qwen3:4b-instruct-2507-q4_K_M`으로 바꾸면 factual proxy 18/22, format proxy 22/22, meta reasoning 0건, 평균 응답 시간 4.625초로 개선됐다.
   - service-tone과 structured data를 붙인 최종 통합 설정은 factual proxy 17/22, format proxy 22/22, meta reasoning 0건, 평균 응답 시간 5.130초였다.

이 선택은 "가장 똑똑한 모델"을 고른 것이 아니라, 본 프로젝트의 목적에 맞게 `검색 품질`, `답변 형식`, `로컬 실행 가능성`, `재현성` 사이의 균형을 맞춘 선택이다.

## 11. 답변 생성 모델 확장 후보

다음 단계에서는 성능 여유에 따라 Qwen3-8B 또는 Qwen3-14B를 비교 후보로 둔다.

Qwen3를 중심 후보로 두는 이유:

- Qwen3 Technical Report는 Qwen3가 thinking mode와 non-thinking mode를 하나의 프레임워크에서 전환할 수 있다고 설명한다.
- 같은 보고서는 Qwen3가 Qwen2.5 대비 언어 지원을 29개에서 119개 언어/방언으로 확장했다고 설명한다.
- 이 특성은 한국어 게임 문서 QA, 오류 분석, 평가 보조에 유리하다.
- 출처: https://arxiv.org/abs/2505.09388

역할별 후보:

| 역할 | 현재/후보 | 사용 목적 |
|---|---|---|
| 초기 답변 생성 | qwen3:4b | 로컬 MVP, baseline/RAG 개선 검증 |
| 최종 답변 생성 | qwen3:4b-instruct-2507-q4_K_M | 서비스 답변 형식 개선, 추론 노출 억제 |
| 답변 생성 확장 | Qwen3-8B-Instruct | 품질 향상과 로컬 실행 현실성의 균형 |
| 고품질 답변/평가 보조 | Qwen3-14B-Instruct | 더 안정적인 추론과 기준별 평가 보조 |
| 안정 baseline | Qwen2.5-7B/14B-Instruct | Qwen3와 이전 세대 비교 |
| 공개 모델 비교군 | Llama-3.1/3.2 계열 | Qwen 계열이 한국어 게임 문서에서 유리한지 비교 |

## 12. 평가자 모델은 보조로만 사용

Qwen3 Thinking mode나 DeepSeek-R1-Distill-Qwen 계열은 평가/오류 분석 보조 후보로 둘 수 있다.

DeepSeek-R1 논문은 강화학습을 통해 reasoning capability를 유도했고, Qwen/Llama 기반 distill 모델도 공개했다고 설명한다.

출처: https://arxiv.org/abs/2501.12948

다만 본 프로젝트의 핵심 평가는 모델 자동 채점이 아니라 기준 정답, evidence, 루브릭 기반 수동 평가다. 평가자 모델은 다음 용도로만 보조적으로 활용하는 편이 안전하다.

- 답변과 evidence의 충돌 후보 찾기
- 환각 의심 문장 표시
- 누락된 조건 후보 찾기
- 평가 메모 초안 작성

최종 점수는 사람이 루브릭 기준으로 확인한다. 이렇게 해야 “모델이 모델을 평가했다”는 약점을 줄일 수 있다.

## 13. 최종 추천 구조

현재 프로젝트와 다음 개선을 합치면 권장 구조는 다음과 같다.

```text
현재 구현:
BM25 heuristic RAG baseline + qwen3:4b
BGE-M3 dense retrieval
structured data
safety gate
service-tone prompt
최종 생성 모델: qwen3:4b-instruct-2507-q4_K_M

성능 확장:
성능 여유 시 Qwen3-8B/14B 비교

평가 보조:
수동 루브릭 평가를 기본으로 하고,
Qwen3 Thinking 또는 DeepSeek-R1-Distill-Qwen은 오류 분석 보조로만 사용
```

보고서/면접용 문장:

```text
본 프로젝트는 최신 게임 문서 기반 QA이므로 단일 LLM의 사전지식보다 검색 기반 근거 제공이 중요하다고 판단했습니다. 먼저 qwen3:4b와 BM25 heuristic 기반 RAG로 baseline 대비 개선을 검증했고, 이후 BGE-M3 embedding retrieval이 top-1 근거 회수와 factual proxy를 개선하는지 비교했습니다. 표형 데이터 오류를 줄이기 위해 구조화 JSON 근거를 추가했고, 최종 답변 형식 문제는 qwen3:4b-instruct-2507과 service-tone prompt로 개선했습니다. 평가는 자동 채점에만 의존하지 않고 기준 정답, evidence, 루브릭 기반 수동 평가를 기본으로 하며, Qwen3 Thinking 또는 DeepSeek-R1 계열은 오류 분석 보조로 활용할 수 있습니다.
```

## 14. 한계와 다음 개선

RAG 적용 후에도 표형 상점 데이터에서는 일부 오류가 남았다.

예:

- 태초 광휘의 의지 가격/구매 제한
- 태초 소울 1개 상자 가격/월 구매 제한

이는 Markdown line chunk가 표의 key-value 관계를 충분히 보존하지 못했기 때문이다. 이 문제를 줄이기 위해 현재는 아이템명, 가격, 구매 제한, 이월 조건을 JSON 형태로 구조화해 검색과 답변에 함께 제공하는 옵션을 추가했다.

남은 개선 과제:

1. Q002~Q004를 중심으로 `RAG only`와 `RAG + structured data`를 같은 루브릭으로 비교 채점한다.
2. Q002처럼 인접 행 조건이 섞이는 사례에 structured record 우선 규칙을 추가한다.
3. `모험가님` 호칭을 포함한 서비스 톤 프롬프트를 별도로 재평가한다.
4. 성능 여유가 있을 경우 Qwen3-8B/14B의 답변 품질과 latency를 비교한다.
5. 평가자 모델은 보조 분석 도구로만 사용하고 최종 평가는 사람이 검토한다.

## 참고문헌

- Chen, J., Xiao, S., Zhang, P., Luo, K., Lian, D., & Liu, Z. (2024). BGE M3-Embedding: Multi-lingual, multi-functionality, multi-granularity text embeddings through self-knowledge distillation. arXiv. https://arxiv.org/abs/2402.03216
- DeepSeek-AI, Guo, D., Yang, D., Zhang, H., et al. (2025). DeepSeek-R1: Incentivizing reasoning capability in LLMs via reinforcement learning. arXiv. https://arxiv.org/abs/2501.12948
- Es, S., James, J., Espinosa-Anke, L., & Schockaert, S. (2023). RAGAS: Automated evaluation of retrieval augmented generation. arXiv. https://arxiv.org/abs/2309.15217
- Liang, P., Bommasani, R., Lee, T., et al. (2022). Holistic Evaluation of Language Models. arXiv. https://arxiv.org/abs/2211.09110
- Yang, A., Li, A., Yang, B., Zhang, B., Hui, B., Zheng, B., et al. (2025). Qwen3 Technical Report. arXiv. https://arxiv.org/abs/2505.09388
