# DeepEval RAG adapter notes

## 목적

이번 단계의 목표는 기존 내부 평가 CSV를 DeepEval이 읽기 쉬운 RAG test case 형태로 고정하는 것이다. DeepEval 자체를 바로 필수 의존성으로 추가하지는 않았다. 평가자 모델, API key, threshold를 먼저 정하지 않은 상태에서 judge 실행까지 묶으면 재현성과 비용 변수가 커지기 때문이다.

추가한 어댑터:

- `scripts/export_deepeval_rag_cases.py`

기본 입력:

- `eval/rag_v2026_06_hybrid_structured_instruct_answers.csv`

기본 출력:

- `eval/deepeval_rag_v2026_06_hybrid_structured_cases.jsonl`
- `eval/deepeval_rag_v2026_06_hybrid_structured_cases.manifest.json`

## DeepEval 필드 매핑

DeepEval 공식 문서의 `LLMTestCase`/RAG metric 구조를 기준으로 아래처럼 매핑했다.

| 내부 CSV | DeepEval case field | 의미 |
|---|---|---|
| `question` | `input` | 사용자 질문 |
| `model_answer` | `actual_output` | 현재 RAG pipeline이 생성한 답변 |
| `gold_answer` | `expected_output` | 기준 정답 또는 비교용 reference answer |
| `retrieved_context` | `retrieval_context` | 모델에게 제공된 검색 근거 block 목록 |
| `evidence` | `metadata.gold_evidence` | 사람이 만든 기준 evidence |
| `question_id`, `doc_id`, `model`, `retriever`, `retrieved_chunk_ids` 등 | `metadata` | 추적과 오류 분석용 메타데이터 |

현재 `run_rag_local_llm_eval.py`의 structured 실행은 `retrieved_context`에 structured context와 chunk context를 합친 실제 prompt context를 기록한다. 어댑터는 이 값을 우선 사용하고, `structured_context`가 누락되어 있을 때만 보강한다.

## 생성 결과

실행 명령:

```powershell
python scripts\export_deepeval_rag_cases.py `
  --answers eval\rag_v2026_06_hybrid_structured_instruct_answers.csv `
  --output eval\deepeval_rag_v2026_06_hybrid_structured_cases.jsonl
```

결과:

| 항목 | 값 |
|---|---:|
| source rows | 20 |
| exported cases | 20 |
| skipped non-success rows | 0 |
| retrieval context blocks min/max/avg | 8 / 9 / 8.1 |

## 추천 DeepEval 평가 항목

다음 단계에서 DeepEval을 실제 실행한다면 우선순위는 아래가 적절하다.

1. `FaithfulnessMetric`: 답변이 `retrieval_context`에 의해 지지되는지 확인한다.
2. `ContextualRelevancyMetric`: 검색된 근거가 질문과 관련 있는지 확인한다.
3. `AnswerRelevancyMetric`: 답변이 질문에 직접 답하는지 확인한다.
4. `ContextualPrecisionMetric` / `ContextualRecallMetric`: 기준 정답 대비 검색 근거의 순위와 누락을 본다.
5. Custom `GEval`: 던파 패치노트용 수동 rubric을 LLM-as-judge rubric으로 옮긴다.

이 순서는 현재 프로젝트의 핵심 실패 모드와 맞다. 지금까지의 proxy는 token/phrase 기반이라 보수적인 false negative가 있었고, DeepEval 계열 judge는 이 중 일부를 “근거는 맞지만 표현이 달라 proxy가 놓친 사례”로 분리하는 데 쓸 수 있다.

## 아직 남은 결정

- evaluator model: OpenAI, local judge, 또는 다른 hosted judge 중 선택해야 한다.
- threshold: 자동 통과/실패 기준은 수동 채점 sample과 맞춰 calibration해야 한다.
- 비용/재현성: judge 결과는 모델 버전과 프롬프트에 영향을 받으므로 manifest와 함께 저장해야 한다.
- 안전성 평가: DeepEval RAG metric은 답변 품질 보조 지표이고, prompt injection/safety gate recall은 별도 safety suite로 계속 추적한다.

## 참고한 공식 문서

- DeepEval test cases: https://deepeval.com/docs/evaluation-test-cases
- Answer relevancy: https://deepeval.com/docs/metrics-answer-relevancy
- Faithfulness: https://deepeval.com/docs/metrics-faithfulness
- Contextual relevancy: https://deepeval.com/docs/metrics-contextual-relevancy
- Contextual precision: https://deepeval.com/docs/metrics-contextual-precision
- Contextual recall: https://deepeval.com/docs/metrics-contextual-recall
