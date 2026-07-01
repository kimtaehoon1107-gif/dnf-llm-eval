# DeepEval RAG adapter notes

## 목적

이번 단계의 목표는 기존 내부 평가 CSV를 DeepEval이 읽기 쉬운 RAG test case 형태로 고정하는 것이다. DeepEval 자체를 바로 필수 의존성으로 추가하지는 않았다. 평가자 모델, API key, threshold를 먼저 정하지 않은 상태에서 judge 실행까지 묶으면 재현성과 비용 변수가 커지기 때문이다.

추가한 어댑터:

- `scripts/export_deepeval_rag_cases.py`
- `scripts/run_deepeval_rag_judge.py`

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

## Judge runner

DeepEval은 optional dependency로 분리했다.

```powershell
python -m pip install -r requirements-deepeval.txt
```

환경 검증용 dry-run:

```powershell
python scripts\run_deepeval_rag_judge.py `
  --dry-run `
  --limit 2 `
  --output eval\deepeval_rag_v2026_06_judge_dry_run.csv `
  --summary-output eval\deepeval_rag_v2026_06_judge_dry_run_summary.csv
```

로컬 Ollama judge 실행 예시:

```powershell
python scripts\run_deepeval_rag_judge.py `
  --limit 3 `
  --metrics faithfulness contextual_relevancy answer_relevancy `
  --judge-model qwen3:4b-instruct-2507-q4_K_M `
  --judge-num-ctx 8192 `
  --output eval\deepeval_rag_v2026_06_hybrid_structured_judge_sample.csv `
  --summary-output eval\deepeval_rag_v2026_06_hybrid_structured_judge_sample_summary.csv `
  --keep-going
```

전체 실행은 `--limit`을 제거하면 된다. `contextual_precision`과 `contextual_recall`은 기준 정답을 함께 쓰는 보조 metric으로, sample 실행이 안정화된 뒤 추가하는 것이 낫다.

DeepEval의 Ollama 기본 context가 4096으로 잡히면 긴 RAG context 문항에서 overflow가 날 수 있다. 그래서 runner 기본값은 `--judge-num-ctx 8192`로 두었다.

## 2026-06-30 실제 judge 실행 결과

실행에 사용한 optional dependency:

- `deepeval==4.0.7`
- `ollama==0.6.2`

주의: `deepeval==4.0.7`은 `click<8.4.0`을 요구한다. 현재 로컬 Python 환경에서는 `huggingface-hub`가 `click>=8.4.0`을 요구한다는 dependency resolver 경고가 발생했다. `huggingface_hub`와 `FlagEmbedding` import는 정상 동작했지만, 장기적으로는 DeepEval 실행을 별도 virtualenv에 격리하는 편이 안전하다. 실제 judge 결과를 만든 뒤 기본 환경은 다시 `pip check`가 통과하도록 원복했다.

실행 명령:

```powershell
python scripts\run_deepeval_rag_judge.py `
  --metrics faithfulness `
  --judge-model qwen3:4b-instruct-2507-q4_K_M `
  --judge-num-ctx 8192 `
  --output eval\deepeval_rag_v2026_06_hybrid_structured_faithfulness_judge.csv `
  --summary-output eval\deepeval_rag_v2026_06_hybrid_structured_faithfulness_judge_summary.csv `
  --keep-going
```

결과:

| metric | cases | scored | passed | errors | avg_score | min_score | max_score |
|---|---:|---:|---:|---:|---:|---:|---:|
| faithfulness | 20 | 20 | 13 | 0 | 0.692 | 0.000 | 1.000 |

threshold 0.7 기준 fail 문항:

- `Q001`: 전리품 상점 가격/구매 제한 해석 오류
- `Q002`: 가격 조정값 해석 오류
- `Q011`: 타이드 바운드 쿨타임 수치 불일치
- `Q012`: 구조화 근거와 chunk 근거 사이의 skill/option 매칭 혼선
- `Q015`: judge reason과 score가 서로 모순됨
- `Q016`: 충전 기능 삭제 외 추가 조작 방식 변경을 생성
- `Q020`: major update 구성요소를 과도하게 "주요 구성요소"로 일반화

해석:

- DeepEval faithfulness는 기존 token/phrase proxy가 놓치거나 애매하게 본 수치/관계 오류를 비교적 잘 잡았다.
- `Q015`처럼 judge reason은 정합성을 말하면서 score는 0.000을 주는 self-consistency 오류가 있다. 따라서 DeepEval 결과는 자동 최종 판정자가 아니라 manual review queue를 정렬하는 보조 신호로 쓰는 것이 맞다.
- 다음 calibration 단계에서는 fail 문항을 사람이 다시 확인하고, judge prompt/model/threshold를 조정한 뒤 `contextual_relevancy`와 `answer_relevancy`를 전체 실행으로 확장한다.

수동 리뷰 결과는 `report/deepeval_faithfulness_manual_review.md`에 정리했다. fail 7건 중 명확한 생성 오류는 `Q001`, 부분 누락은 `Q012`, 나머지 5건은 judge false positive 또는 rubric 과민 반응으로 분류했다.

## 2026-07-01 compact evidence calibration

Structured fix 이후 `scripts/export_deepeval_rag_cases.py`에 `--context-mode compact`와 `--compact-top-k`를 추가했다. Compact mode는 `structured_context`, 사람이 만든 `evidence`, top retrieved chunk를 합쳐 judge context를 줄인다.

`eval/rag_v2026_06_hybrid_structured_fix_instruct_answers.csv` 기준 결과:

| setting | context blocks avg | faithfulness pass | avg score | errors |
|---|---:|---:|---:|---:|
| compact top-1 | 2.45 | 12 / 20 | 0.690 | 0 |
| compact top-3 | 4.45 | 14 / 20 | 0.735 | 0 |

Top-3가 top-1보다 안정적이었다. 다만 top-3의 남은 fail 6건은 수동 리뷰에서 모두 생성 수정 대상이 아닌 judge false positive 또는 self-consistency 오류로 분류했다. 상세 내역은 `report/deepeval_compact_evidence_calibration_v2026_06.md`에 정리했다.

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
