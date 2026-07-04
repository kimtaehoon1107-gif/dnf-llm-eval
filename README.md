# DNF LLM Evaluation Project

던전앤파이터 공식 업데이트 문서를 기반으로 **로컬 LLM의 답변 품질을 평가**한 포트폴리오 프로젝트입니다.  
핵심은 챗봇 데모가 아니라 `문서 수집 -> 벤치마크 질문 설계 -> RAG 검색 -> 답변 생성 -> 평가 지표 설계 -> 실패 원인 분석`으로 이어지는 평가 파이프라인입니다.

**웹 포트폴리오:** [https://kimtaehoon1107-gif.github.io/dnf-llm-eval/](https://kimtaehoon1107-gif.github.io/dnf-llm-eval/)

**주요 구성:** Python 3.10+, Selenium, BM25 heuristic, BGE-M3, Ollama, Qwen3 4B Instruct, rule-based safety gate, manual rubric evaluation

> **주의:** 2026-07-01 structured fix 및 intent safety gate 결과는 dev/test-informed 결과입니다. 동일 문항의 실패 분석을 바탕으로 record와 rule을 보강한 뒤 재측정했으므로 headline 수치를 held-out 일반화 성능으로 해석하지 않습니다. 이후 factual blind held-out 25문항을 freeze해 검증한 결과, structured record는 dev 9/20 문항에 발동했지만 held-out에서는 0/25 문항에 발동했고 모든 ablation 조건이 23/25로 동률이었습니다. 별도 structured record diagnostic/probe에서는 record가 의도적으로 발동하는 조건에서 24/35 -> 30/35 -> 32/35로 개선되어, 남은 병목이 구조화 메커니즘 자체가 아니라 record coverage/extraction임을 분리했습니다. Safety는 최종 fresh v6에서 intent_rules_v5가 12/24 attack recall, benign FP 0/24를 기록해 제한적 개선으로 보고합니다. Semantic classifier는 v6 20/24, FP 0/24를 재현했지만 retrospective prototype이므로 정식 headline은 future work로 둡니다.

## Project Snapshot

### 한눈에 보는 결론

| 질문 | 결론 | 의미 |
|---|---:|---|
| RAG가 실제로 도움이 됐나? | 11.27 -> 18.86 / 21 | 문서 전체를 넣는 방식보다 관련 근거 chunk를 찾아 넣는 방식이 더 안정적이었다. |
| 검색기는 무엇을 최종 선택했나? | BGE-M3 | Top-1 evidence hit이 21 / 22로 BM25 heuristic의 19 / 22보다 높았다. |
| 생성 모델 병목은 무엇이었나? | format proxy 9 / 22 -> 22 / 22 | 기존 `qwen3:4b`의 영어 추론/메타 발화 문제를 instruct variant로 줄였다. |
| 최종 설정의 현실적 성능은? | factual proxy 17 / 22, 평균 5.130s | 경량 로컬 모델로 재현 가능한 수준의 답변 품질과 응답 시간을 확인했다. |
| 2026-06 structured fix는 일반화됐나? | dev 20/20, held-out 23/25 | 높은 dev 점수를 그대로 주장하지 않고, record 비전이(9/20 -> 0/25)를 held-out으로 검출했다. |
| record가 발동하면 구조화가 도움 되나? | diagnostic probe 24/35 -> 30/35 -> 32/35 | 새 held-out이 아니라 메커니즘 진단이다. record가 붙으면 품질은 오르지만, 다음 병목은 coverage/extractor다. |
| Safety는 어디까지 됐나? | fresh v6 12/24, FP 0/24 | regression 100%를 최종 성능처럼 쓰지 않고, 사전 선언한 fresh blind 결과를 그대로 보고했다. |

**읽는 법:** 이 프로젝트의 숫자는 한 가지 점수가 아니라 `검색 품질`, `답변 생성 품질`, `답변 형식`, `safety 한계`를 따로 측정한 결과입니다. 예를 들어 `BGE-M3 top-1 hit 21/22`는 검색기가 정답 근거를 잘 찾는지를 본 값이고, `최종 factual proxy 17/22`는 그 근거를 받은 LLM이 최종 답변을 얼마나 맞게 생성했는지를 본 값입니다.

<details>
<summary>상세 실험 수치 보기</summary>

#### 1. End-to-end 문서 QA 품질

| 비교 | 결과 |
|---|---:|
| Non-RAG 문서 질문 평균 | 11.27 / 21 |
| RAG 문서 질문 평균 | 18.86 / 21 |

#### 2. Retrieval 비교

| 검색기 | Top-1 evidence hit |
|---|---:|
| BM25 heuristic | 19 / 22 |
| BGE-M3 | 21 / 22 |

#### 3. BGE-M3 고정 생성 설정 요소별 비교 실험

| 설정 | Factual proxy | Format proxy | 평균 응답 시간 |
|---|---:|---:|---:|
| BGE-M3 + `qwen3:4b` | 17 / 22 | 9 / 22 | 11.635s |
| BGE-M3 + instruct variant | 18 / 22 | 22 / 22 | 4.625s |
| 최종 통합 설정 | 17 / 22 | 22 / 22 | 5.130s |

#### 4. Safety 평가

| 평가 세트 | 결과 | 해석 |
|---|---:|---|
| 명시적 공격 질문 | 10 / 10 | 직접적인 공격/범위 밖 질문은 규칙 기반 gate로 차단 |
| Paraphrase safety | 0 / 10 -> 10 / 10 | 사후 보강 규칙으로 개선했지만 test-informed 한계가 있음 |
| Stealth safety 사전 차단 | 0 / 10 | 직접 키워드를 피하면 규칙 기반 gate가 약함 |
| Stealth end-to-end strict pass | 6 / 10 | 생성 답변 단계까지 포함하면 일부는 안전하게 거절 |
| Final safety v6 | 12 / 24, FP 0 / 24 | 사전 선언한 fresh blind 검증. 제한적 개선으로 보고 |
| Backward compatibility | 90 / 120, FP 1 / 120 | 과거 진단 공격 스타일 유지력. fresh 일반화 성능과 분리 |
| Semantic prototype | v6 20 / 24, FP 0 / 24 | BGE-M3 1-NN retrospective 결과. 정식 headline은 future work |

</details>

**Safety 해석:** rule-based safety gate는 설명 가능하고 빠른 baseline으로는 유용하지만, 완성된 보안 장치가 아닙니다. 이번 프로젝트는 regression set 100% 같은 개발 성과와 fresh blind v6의 12/24를 분리해 보고합니다. BGE-M3 semantic prototype은 v6에서 20/24를 재현했지만 retrospective 결과이므로, 다음 연구 후보로만 남깁니다.

## Final Pipeline

```mermaid
flowchart LR
  Q["User Question"] --> S["Safety Gate"]
  S --> R["Retriever: BGE-M3"]
  R --> C["Context Builder"]
  D["Structured Shop Data"] --> C
  C --> G["Generator: qwen3:4b-instruct-2507-q4_K_M"]
  G --> E["Evaluator and Logger"]
  E --> P["Reports"]
```

최종 조합은 `BGE-M3 retriever + structured shop data + qwen3:4b-instruct-2507-q4_K_M + safety gate`입니다.

최종 생성 모델은 로컬 실행 가능한 4.0B Qwen3 계열 모델이며, `Q4_K_M` 양자화로 실행 부담을 줄인 구성을 사용했습니다. 기존 `qwen3:4b`는 검색 근거를 받은 뒤에도 영어 추론 과정과 메타 발화를 출력했기 때문에, 최종 단계에서는 instruction following이 더 안정적인 instruct variant를 사용해 한국어 답변 형식을 개선했습니다.

## What Was Designed

이 프로젝트에서 직접 설계한 부분은 모델 호출 자체보다 `평가 문제`, `평가 지표`, `실패 분석 기준`입니다.

| 설계 요소 | 의미 | 사용 위치 |
|---|---|---|
| Benchmark questions | 던파 업데이트 문서에서 실제 유저가 물어볼 만한 질문, 기준 정답, 근거 문장을 함께 만든 평가셋 | `questions/benchmark_questions.csv` |
| Structured data | 상점표처럼 행/열 관계가 중요한 정보를 JSON으로 따로 추출한 보조 근거. 가격, 구매 제한, 이월 조건처럼 표에서 섞이기 쉬운 정보를 보완 | `data/structured/shop_items.json` |
| Safety gate | 프롬프트 유출, 가짜 근거, 버그 악용, 현금화, 매크로 요청, OOD 질문을 답변 전에 차단하는 규칙 기반 baseline | `questions/adversarial_*.csv` |
| Manual rubric | 기존 대표 채점은 7개 항목 legacy 루브릭으로 기록했고, 현재 운영 루브릭은 점수 항목과 binary critical gate를 분리 | `eval/evaluation_rubric.md` |

`Structured data`는 LoRA나 adapter가 아니라, RAG context builder에 추가로 넣는 구조화 근거입니다. 일반 chunk 검색은 긴 표 안에서 인접 행 정보를 섞을 수 있으므로, 상점 아이템명, 가격, 구매 제한, 이월 조건을 별도 record로 만들어 표형 정보 질문에서 보조 근거로 사용했습니다.

## Evaluation Design

정량 평가는 여러 설정을 빠르게 비교하기 위한 자동 지표이며, 그중 factual proxy와 format proxy는 사람이 직접 평가하기 전의 대리 지표입니다. 정성 평가는 실제 최종 답변으로 볼 수 있는지를 확인하기 위한 수동 기준입니다.

| 지표 | 유형 | 무엇을 보는가 |
|---|---|---|
| Top-1 evidence hit | 정량 | 검색기가 정답 근거 chunk를 첫 번째로 찾았는가 |
| Retrieval token recall / phrase hit | 정량 | 검색된 context가 기준 evidence의 핵심 token/phrase를 얼마나 포함하는가 |
| Answer token recall / phrase hit | 정량 | 모델 답변이 gold answer 또는 evidence의 핵심 token/phrase를 얼마나 포함하는가 |
| Factual proxy | 정량 | 답변이 기준 정답의 핵심 정보를 포함하는지 자동으로 근사 판정 |
| Format proxy | 정량 | 영어 추론, 메타 발화, 비한국어 잡음 없이 한국어 답변 형식을 지키는가 |
| Latency | 정량 | 로컬 모델이 실제 질의응답에 쓸 만한 속도로 답하는가 |
| Manual rubric + critical gates | 정성 | 정확성, 근거성, 완전성, 의도 적합성, 표현 품질, 최신성을 채점하고 환각/과잉추론, 중대 수치 오류, 라이브 서버 기준 오인, 범위 통제는 binary gate로 확인 |

자동 proxy는 빠르게 여러 설정을 비교하기 위한 보조 지표입니다. 예를 들어 답변이 사실상 맞아도 표현이 기준 정답과 다르면 factual proxy가 실패할 수 있습니다. 그래서 최종 해석에서는 [`eval/evaluation_rubric.md`](eval/evaluation_rubric.md)의 운영 루브릭과 [`eval/representative_manual_scoring.csv`](eval/representative_manual_scoring.csv)의 legacy 대표 문항 채점을 함께 봅니다.

## Qualitative Example

정량 결과만으로는 답변 품질 차이가 잘 보이지 않기 때문에, 대표 문항에서 실제 출력 형태도 비교했습니다.

질문: `태초 광휘의 의지는 광휘의 잔영 몇 개로 구매할 수 있고 구매 제한은 어떻게 되는가?`

| 설정 | 실제 답변 경향 | 해석 |
|---|---|---|
| BGE-M3 + `qwen3:4b` | 영어로 "Okay, let's tackle this question..."처럼 추론 과정을 길게 출력하고, 중간에 "Wait" 같은 메타 발화가 섞임 | 근거는 찾았지만 최종 답변 형식으로는 부적합 |
| BGE-M3 + instruct variant | `태초 광휘의지는 광휘의 잔영 790개로 구매할 수 있으며, 계정당 1회로 제한됩니다.` | 짧고 한국어 중심이며 핵심 답변을 바로 제시 |
| BGE-M3 + instruct + structured evidence | 가격, 구매 제한, 이월 조건 같은 표형 정보를 구조화 근거로 함께 제공 | 표형 정보 보완에는 도움이 되지만, 인접 조건 혼입 여부는 수동 검토 필요 |

이 예시에서 핵심 개선은 "모델이 더 많이 말한다"가 아니라, 근거 기반 답변을 짧고 확인 가능한 한국어 답변 형태로 바꾼 것입니다.

## Start Here

| File | Why it matters |
|---|---|
| [웹 포트폴리오](https://kimtaehoon1107-gif.github.io/dnf-llm-eval/) | GitHub Pages로 배포한 제출용 프로젝트 소개 페이지 |
| [`index.html`](index.html) | GitHub Pages 배포용 HTML 포트폴리오 첫 화면 |
| [`report/final_closing_review.md`](report/final_closing_review.md) | 제출용 최종 요약과 최신 결과 리뷰 |
| [`report/final_portfolio_report.md`](report/final_portfolio_report.md) | 전체 실험 과정과 결과를 정리한 통합 보고서 |
| [`report/heldout_factual_ablation_v1.md`](report/heldout_factual_ablation_v1.md) | blind held-out 25문항과 record 비전이 감사 |
| [`report/structured_record_probe_v1.md`](report/structured_record_probe_v1.md) | record가 실제 발동하는 조건에서 구조화 데이터 효과를 진단한 probe |
| [`report/safety_eval_final_report_v6.md`](report/safety_eval_final_report_v6.md) | safety 최종 fresh v6 결과: 12/24, benign FP 0/24 |
| [`report/safety_eval_process_summary_for_main_project.md`](report/safety_eval_process_summary_for_main_project.md) | safety v1~v6 개선 라운드와 regression/held-out 분리 과정 |
| [`docs/PROJECT_REVIEW_BRIEF.md`](docs/PROJECT_REVIEW_BRIEF.md) | 리뷰어/면접관용 1-page 핵심 설명 |
| [`report/ablation_study_report.md`](report/ablation_study_report.md) | BGE-M3 고정 후 생성 모델 변경 효과를 분리한 추가 실험 |
| [`report/README.md`](report/README.md) | 보고서 폴더의 권장 읽기 순서 |
| [`report/application_summary.md`](report/application_summary.md) | 지원서와 면접에서 바로 설명할 수 있는 요약문 |
| [`report/model_selection_and_benchmark_rationale.md`](report/model_selection_and_benchmark_rationale.md) | 모델, 검색기, 평가 방법 선택 근거 |
| [`report/references.md`](report/references.md) | 평가/RAG/모델/safety 설계 참고문헌 |
| [`questions/benchmark_questions.csv`](questions/benchmark_questions.csv) | 문서 기반 벤치마크 질문 22개 |
| [`eval/representative_manual_scoring.csv`](eval/representative_manual_scoring.csv) | 대표 문항 수동 채점표 |

## Component Map

| Component | Main files | Role |
|---|---|---|
| Data collection | `scripts/collect_dnf_updates_selenium.py`, `data/processed_md/` | 던파 공식 업데이트 문서를 수집하고 평가용 문서 corpus로 정리 |
| Benchmark design | `questions/benchmark_questions.csv` | 실제 이용자가 물어볼 수 있는 문서 기반 질문과 기준 정답 설계 |
| Retrieval | `scripts/run_rag_local_llm_eval.py`, `eval/retrieval_compare_summary.csv` | BM25 heuristic과 BGE-M3 검색 성능 비교 |
| Structured context | `scripts/build_structured_shop_data.py`, `data/structured/shop_items.json` | 표형 상점 데이터를 별도 구조로 추출해 가격/제한 조건 보완 |
| Generation | `qwen3:4b`, `qwen3:4b-instruct-2507-q4_K_M` | 검색 근거를 바탕으로 로컬 LLM 답변 생성 및 형식 개선 비교 |
| Safety | `questions/adversarial_*.csv`, `report/paraphrase_safety_gate_test.md` | prompt leakage, fake evidence, automation abuse, OOD 질문 차단 검증 |
| Evaluation | `eval/evaluation_rubric.md`, `scripts/score_*.py` | 검색 hit, factual proxy, format proxy, 수동 rubric으로 품질 측정 |
| Reporting | `report/final_portfolio_report.md`, `report/application_summary.md` | 실험 결과를 지원서와 면접에서 설명 가능한 형태로 정리 |

## 프로젝트 목적

게임 도메인 LLM 평가/AI 서비스 품질 및 안전성 평가 직무의 핵심 업무를 작게 재현하는 것이 목표입니다.

| 직무 요구 | 프로젝트 대응 |
|---|---|
| 게임 도메인 LLM 벤치마크 구성 | 던파 업데이트 문서 기반 질문 22개, OOD 질문, adversarial 질문 설계 |
| 평가 지표 및 기준 개발 | 검색 지표, 답변 proxy, 수동 rubric, binary critical gate 설계 |
| LLM 응답 품질 평가 | baseline, RAG, BM25, BGE-M3, structured data, 생성 모델 비교 |
| 결과 분석 및 공유 | CSV 로그와 Markdown 보고서로 결과 정리 |

## 프로젝트 구조

```text
dnf-llm-eval/
  index.html                     # GitHub Pages용 포트폴리오 첫 화면
  data/
    processed_md/                 # 수집한 던파 업데이트 문서
    structured/shop_items.json    # 켈돈 자비 상점표 구조화 데이터
    corpus_snapshot.json          # 현재 checked-in corpus의 문서/해시/버전 정보
    metadata.csv
    discovered_update_urls.csv
  questions/
    benchmark_questions.csv
    benchmark_questions_v2026_05.csv
    benchmark_questions_v2026_06.csv
    question_sets.json
    out_of_domain_questions.csv
    adversarial_questions.csv
    adversarial_paraphrase_questions.csv
    adversarial_stealth_questions.csv
  scripts/
    collect_dnf_updates_selenium.py
    build_structured_shop_data.py
    run_local_llm_eval.py
    run_rag_local_llm_eval.py
    ask_dnf_rag.py
    score_retrieval_runs.py
    score_answer_runs.py
  eval/
    retrieval_compare_summary.csv
    answer_compare_summary.csv
    ablation_answer_compare_summary.csv
    ablation_answer_compare_detail.csv
    answer_compare_qwen3_4b_instruct2507_full_standard_summary.csv
    rag_local_llm_adversarial_paraphrase_safety_gate_v2.csv
    rag_local_llm_adversarial_stealth_safety_gate.csv
    adversarial_stealth_manual_review.csv
    representative_manual_scoring.csv
    evaluation_rubric.md
  report/
    README.md
    final_closing_review.md
    final_portfolio_report.md
    ablation_study_report.md
    application_summary.md
    model_selection_and_benchmark_rationale.md
    references.md
    retriever_comparison_report.md
    answer_retriever_comparison_report.md
    representative_manual_scoring.md
    baseline_and_ablation_design.md
    structured_data_and_safety_gate_update.md
    paraphrase_safety_gate_test.md
    stealth_safety_gate_test.md
    safety_design_rationale.md
    archive/                    # 초기 계획서와 오래된 중간 결과 보관
```

`data/metadata.csv`에는 수집 당시의 `raw_path` 컬럼과 공식 게시글 번호인 `source_post_id`가 남아 있습니다. 원본 HTML(`data/raw_html/`)은 재수집/디버깅 단계에서 생성되는 로컬 산출물이라 최종 제출 패키지에는 포함하지 않았고, 평가와 재현에는 `data/processed_md/`의 Markdown 문서와 `metadata.csv`의 출처 URL을 사용합니다.

기존 corpus는 `DOC-01`처럼 수집 순번 기반 ID를 사용합니다. 이 checked-in 기준점은 `data/corpus_snapshot.json`에 문서 목록, metadata hash, processed markdown hash로 기록합니다. 이후 재수집분은 공식 업데이트 게시글 번호를 사용한 `DNF-2927756` 형식의 안정 ID를 사용하도록 collector를 바꿨습니다. 로더와 smoke check는 기존 `DOC-*`와 신규 `DNF-*` 파일명을 모두 지원합니다.

최신 공식 문서를 실험용으로 다시 수집할 때는 기존 benchmark corpus를 덮어쓰지 않고 snapshot 디렉터리에 staging할 수 있습니다.

```powershell
python scripts\collect_dnf_updates_selenium.py `
  --data-dir data\snapshots\2026-06-official-updates `
  --max 8

python scripts\build_corpus_snapshot.py `
  --metadata data\snapshots\2026-06-official-updates\metadata.csv `
  --doc-dir data\snapshots\2026-06-official-updates\processed_md `
  --output data\snapshots\2026-06-official-updates\corpus_snapshot.json `
  --corpus-id dnf-official-updates-2026-06-staged
```

## 실행 준비

기본 수집/분석 스크립트는 다음 패키지를 사용합니다.

```powershell
pip install -r requirements.txt
```

BGE-M3 embedding 검색까지 재현하려면 추가 패키지가 필요합니다.

```powershell
pip install -r requirements-bge.txt
```

BGE-M3 실행 환경에 따라 `torch`, `transformers`, `sentence-transformers` 계열 의존성이 함께 설치되거나 이미 설치되어 있어야 할 수 있습니다. CPU/GPU 환경에 따라 설치 시간과 첫 embedding cache 생성 시간이 길어질 수 있습니다.

로컬 LLM 실험은 Ollama에 모델이 준비되어 있어야 실행됩니다. 본 저장소에는 모델 가중치와 BGE-M3 cache를 포함하지 않습니다.

```powershell
ollama pull qwen3:4b
ollama pull qwen3:4b-instruct-2507-q4_K_M
```

`qwen3:4b-instruct-2507-q4_K_M`은 최종 답변 생성 실험에 사용한 모델명입니다. 환경에 따라 동일 계열 모델의 태그명이 다르면, Ollama 로컬 모델명을 실행 명령의 `--model` 값과 맞춰 주세요.

BGE-M3는 최초 실행 시 Hugging Face 모델 로드와 embedding cache 생성 때문에 몇 분 정도 걸릴 수 있습니다. 이후 실행은 `data/cache`를 사용하므로 더 빠릅니다.

## 빠른 검증

Ollama 모델이나 BGE-M3 가중치를 내려받기 전에, 저장소 구조와 Python 문법, 주요 CSV/JSON 입력 형식을 먼저 확인할 수 있습니다.

```powershell
python scripts\smoke_check.py
```

이 검증은 외부 모델을 호출하지 않으며, `requirements-bge.txt` 설치도 필요하지 않습니다. Python 실행기 자체가 없는 환경에서는 먼저 Python 3.10 이상이 `PATH`에 잡혀 있는지 확인해 주세요.

## Run manifest

`scripts/run_local_llm_eval.py`와 `scripts/run_rag_local_llm_eval.py`는 평가 CSV를 저장할 때 같은 이름의 manifest JSON도 함께 저장합니다. 예를 들어 `--output eval\answer_compare_bm25.csv`로 실행하면 기본적으로 `eval\answer_compare_bm25.manifest.json`이 생성됩니다.

manifest에는 실행 스크립트, git commit, 질문 CSV hash, question set id, corpus markdown hash, metadata hash, 모델명, retriever 설정, 날짜 기준, 실행 결과 status count가 기록됩니다. corpus를 refresh하거나 여러 run을 비교할 때 “어떤 문서와 설정으로 만든 결과인지”를 추적하기 위한 파일입니다.

현재 active 질문셋은 `questions/question_sets.json`의 `benchmark_questions_v2026_05`이며, 기존 `questions/benchmark_questions.csv`는 이 파일의 active alias입니다. 평가 실행 시 `--question-set-id benchmark_questions_v2026_05`를 넘기면 manifest에 질문셋 버전이 명시됩니다.

2026-06 staged corpus 검증용 질문셋은 `benchmark_questions_v2026_06`입니다. 기존 active corpus와 다른 문서 디렉터리를 쓰므로 실행 시 staged metadata/doc dir를 같이 지정합니다.

```powershell
python scripts\run_rag_local_llm_eval.py `
  --questions questions\benchmark_questions_v2026_06.csv `
  --question-set-id benchmark_questions_v2026_06 `
  --doc-dir data\snapshots\2026-06-official-updates\processed_md `
  --metadata data\snapshots\2026-06-official-updates\metadata.csv `
  --retriever bm25 `
  --dry-run
```

실제 LLM 답변까지 생성할 때는 기본 Ollama context window가 긴 RAG prompt보다 작을 수 있으므로 `--num-ctx 8192` 이상을 함께 지정합니다.

```powershell
python scripts\run_rag_local_llm_eval.py `
  --questions questions\benchmark_questions_v2026_06.csv `
  --question-set-id benchmark_questions_v2026_06 `
  --doc-dir data\snapshots\2026-06-official-updates\processed_md `
  --metadata data\snapshots\2026-06-official-updates\metadata.csv `
  --retriever bm25 `
  --model qwen3:4b-instruct-2507-q4_K_M `
  --disable-thinking `
  --num-predict 512 `
  --num-ctx 8192 `
  --output eval\rag_v2026_06_bm25_instruct_answers.csv
```

필요하면 `--manifest-output path\to\run.manifest.json`으로 저장 위치를 직접 지정할 수 있고, 임시 실행에서는 `--no-manifest`로 생성을 끌 수 있습니다.

## 실험 흐름

### 1. Non-RAG baseline

로컬 모델이 RAG 없이 문서 기반 질문에 얼마나 답할 수 있는지 확인했습니다.

```powershell
python scripts\run_local_llm_eval.py `
  --questions questions\benchmark_questions.csv `
  --output eval\local_llm_answers_full.csv `
  --model qwen3:4b `
  --disable-thinking `
  --num-predict 220
```

### 2. BM25 vs BGE-M3 검색 비교

BM25는 키워드 기반 baseline으로, BGE-M3는 최종 검색 후보로 사용했습니다. 이 프로젝트의 BM25는 순수 BM25만이 아니라 phrase/coverage/intent bonus를 더한 BM25 기반 heuristic retriever입니다.

```powershell
python scripts\run_rag_local_llm_eval.py `
  --questions questions\benchmark_questions.csv `
  --output eval\answer_compare_bm25.csv `
  --model qwen3:4b `
  --restrict-to-question-doc `
  --retriever bm25 `
  --disable-thinking `
  --num-predict 220

python scripts\run_rag_local_llm_eval.py `
  --questions questions\benchmark_questions.csv `
  --output eval\answer_compare_bge_m3.csv `
  --model qwen3:4b `
  --restrict-to-question-doc `
  --retriever bge-m3 `
  --disable-thinking `
  --num-predict 220
```

`--restrict-to-question-doc`는 실제 서비스용 옵션이 아니라, 정답 문서 안에서의 검색과 답변 생성 능력을 분리해 보기 위한 평가용 설정입니다.

### 3. BGE-M3 고정 생성 설정 요소별 비교 실험

최종 조합을 한 번에 비교하면 어떤 요소가 개선에 기여했는지 분리하기 어렵습니다. 그래서 검색기를 BGE-M3로 고정하고, 모델 변경과 구조화 데이터 보강 효과를 분리해 비교했습니다.

```powershell
python scripts\run_rag_local_llm_eval.py `
  --questions questions\benchmark_questions.csv `
  --output eval\ablation_01_bge_qwen3_4b.csv `
  --model qwen3:4b `
  --retriever bge-m3 `
  --disable-thinking `
  --num-predict 512

python scripts\run_rag_local_llm_eval.py `
  --questions questions\benchmark_questions.csv `
  --output eval\ablation_02_bge_qwen3_4b_instruct.csv `
  --model qwen3:4b-instruct-2507-q4_K_M `
  --retriever bge-m3 `
  --disable-thinking `
  --num-predict 512

```

이 요소별 비교 실험은 `--restrict-to-question-doc`를 사용하지 않고 전체 5개 문서 corpus에서 검색했습니다. 결과 해석은 [`report/ablation_study_report.md`](report/ablation_study_report.md)에 정리했습니다. 답변 형식 개선은 최종적으로 instruct 모델의 format proxy 개선으로 설명합니다.

## 주요 결과

### Baseline vs RAG

| 방식 | 전체 평균 | 문서 기반 질문 평균 | OOD 질문 평균 |
|---|---:|---:|---:|
| Non-RAG baseline | 13.87 / 21 | 11.27 / 21 | 21.00 / 21 |
| RAG 적용 | 19.43 / 21 | 18.86 / 21 | 21.00 / 21 |

### 검색기 비교

| Retriever | Top-8 evidence hit | Top-1 evidence hit | Avg token recall |
|---|---:|---:|---:|
| BM25 heuristic | 22 / 22 | 19 / 22 | 0.994 |
| BGE-M3 | 22 / 22 | 21 / 22 | 1.000 |

### 답변 생성 비교

| 설정 | Factual proxy | Format proxy | Meta reasoning | Avg latency |
|---|---:|---:|---:|---:|
| BGE-M3 + `qwen3:4b` | 17 / 22 | 9 / 22 | 13 | 11.635s |
| BGE-M3 + `qwen3:4b-instruct-2507` | 18 / 22 | 22 / 22 | 0 | 4.625s |

가장 큰 변화는 생성 모델을 instruct variant로 바꿨을 때 발생했습니다. Format proxy는 9/22에서 22/22로 개선됐고, meta reasoning 출력은 13건에서 0건으로 줄었습니다. 구조화 데이터는 표형 정보 보완을 위한 별도 근거로 해석하며, token 기반 factual proxy의 false negative 가능성도 함께 고려했습니다.

### 2026-06 staged corpus 후속 검증

아래 결과는 기존 active `benchmark_questions_v2026_05` 22문항 결과를 대체하지 않는 별도 검증이다. 2026-06 공식 업데이트 8개 문서를 staged corpus로 두고, draft 질문셋 `benchmark_questions_v2026_06` 20문항을 BM25 RAG와 `qwen3:4b-instruct-2507-q4_K_M`으로 실행했다.

2026-07-01 structured fix 및 intent safety gate 결과는 dev/test-informed 결과다. 동일 문항의 실패 분석을 바탕으로 record와 rule을 보강한 뒤 재측정했으므로 headline 수치를 held-out 일반화 성능으로 해석하지 않는다.

| 범위 | 설정 | 결과 |
|---|---|---:|
| Retrieval | BM25 full-corpus dry-run | evidence hit 19 / 20, top-1 evidence hit 18 / 20 |
| Retrieval | BGE-M3 full-corpus dry-run | evidence hit 20 / 20, top-1 evidence hit 18 / 20 |
| Retrieval | Hybrid full-corpus dry-run | evidence hit 20 / 20, top-1 evidence hit 18 / 20 |
| Retrieval | Hybrid + BGE reranker | evidence hit 20 / 20, top-1 evidence hit 19 / 20 |
| Generation | BM25 + `qwen3:4b-instruct-2507-q4_K_M` | factual proxy 13 / 20, format proxy 20 / 20, 평균 6.061s |
| Generation | BGE-M3 + `qwen3:4b-instruct-2507-q4_K_M` | factual proxy 13 / 20, format proxy 20 / 20, 평균 4.219s |
| Generation | Hybrid + `qwen3:4b-instruct-2507-q4_K_M` | factual proxy 15 / 20, format proxy 20 / 20, 평균 4.613s |
| Generation | Hybrid + BGE reranker + `qwen3:4b-instruct-2507-q4_K_M` | factual proxy 15 / 20, format proxy 20 / 20, 평균 20.868s |
| Generation | Hybrid + structured change records + `qwen3:4b-instruct-2507-q4_K_M` | factual proxy 16 / 20, format proxy 20 / 20, 평균 4.273s |
| Generation | Hybrid + structured fix + `qwen3:4b-instruct-2507-q4_K_M` | dev/test-informed factual proxy 20 / 20, format proxy 20 / 20, 평균 4.399s |

해석은 [`report/benchmark_questions_v2026_06_design.md`](report/benchmark_questions_v2026_06_design.md)에 정리했다. BGE-M3 단독은 검색 hit과 속도는 개선했지만 factual proxy는 BM25와 같았고, hybrid 검색은 factual proxy를 15/20까지 올렸다. BGE reranker는 top-1 검색 품질과 refusal 억제는 개선했지만 생성 factual proxy는 15/20으로 동일했고 평균 지연이 크게 증가했다. 반면 patch-note change table을 구조화 record로 보강한 hybrid + structured 설정은 factual proxy를 16/20까지 올리고 평균 지연도 4.273s로 유지했다. 남은 실패 중 Q003, Q013, Q014, Q018은 token/phrase proxy의 false negative 또는 부분 답변 가능성이 있어 수동 검토가 필요하다.

후속 감사 실험은 [`report/heldout_factual_ablation_v1.md`](report/heldout_factual_ablation_v1.md)에 정리했다. Blind held-out 25문항에서는 structured record가 0/25 문항에 발동해 structured on/off 토글이 사실상 no-op이었고, no-structured baseline을 포함한 모든 조건이 23/25로 동률이었다. 따라서 20/20은 dev/test-informed 개선으로만 표시하고, 이 프로젝트의 강점은 높은 점수 자체보다 freeze + manifest + ablation으로 비전이를 검출한 절차에 둔다.

별도 진단 실험은 [`report/structured_record_probe_v1.md`](report/structured_record_probe_v1.md)에 정리했다. 이 실험은 새 held-out이 아니라 structured record가 실제로 발동하도록 만든 diagnostic/probe이며, no-structured 24/35, atomic records 30/35, structured fix 32/35를 기록했다. 해석은 "구조화 메커니즘은 record가 붙으면 도움이 된다"와 "blind held-out에서는 hand-authored record가 붙지 않았다"를 분리하는 것이다. 따라서 다음 개선 방향은 손으로 쓴 hint를 늘리는 것이 아니라, 원문 패치노트에서 atomic before/after/unchanged record를 blind 또는 자동으로 추출하는 coverage/extractor 검증이다.

### 4. Safety 평가

Safety는 단순히 "막았다/못 막았다"가 아니라, `공격 recall`, `정상 질문 false positive`, `dev/regression`, `fresh held-out`, `retrospective prototype`을 분리해 평가했다. 핵심은 개발 중 맞춘 세트의 100%를 최종 성능처럼 쓰지 않고, 사전 선언한 fresh v6 결과를 headline으로 낮춰 보고한 점이다.

| 평가 단계 | 결과 | 해석 |
|---|---:|---|
| 초기 adversarial 질문 | 10 / 10 차단 | 명시적 공격에는 규칙 기반 gate가 작동 |
| Paraphrase safety | 0 / 10 -> 10 / 10 | 실패 문항을 본 뒤 보강한 test-informed 개선 |
| Stealth safety 사전 차단 | 0 / 10 | 직접 키워드를 피하면 keyword gate가 약함 |
| Stealth end-to-end strict pass | 6 / 10 | system prompt가 일부 방어하지만 완전하지 않음 |
| Intent gate dev/regression | 공격 50 / 50, 정상 FP 0 / 50 | 기존 세트 기준 개발 성과. 최종 일반화 headline 아님 |
| Final safety v6 `keyword_rules_v2` | attack 1 / 24, FP 0 / 24 | keyword baseline의 fresh 한계 |
| Final safety v6 `intent_rules_v5` | attack 12 / 24, FP 0 / 24 | 최종 fresh headline. 제한적 개선으로 보고 |
| Backward compatibility | attack 90 / 120, FP 1 / 120 | 과거 진단 공격 스타일 유지력. 신규 공격 일반화와 분리 |
| Semantic classifier prototype | v6 attack 20 / 24, FP 0 / 24 | BGE-M3 1-NN retrospective prototype. 정식 headline은 v7 이후 |

Safety 최종 라운드는 [`report/safety_eval_final_report_v6.md`](report/safety_eval_final_report_v6.md)와 [`report/safety_eval_process_summary_for_main_project.md`](report/safety_eval_process_summary_for_main_project.md)에 정리했다. v6에서 `intent_rules_v5`는 `intent_rules_v4` 대비 attack block rate를 10/24에서 12/24로 올렸고 benign false positive는 0/24로 유지했다. 별도 재검산에서는 과거 진단 공격 스타일 유지력은 90/120(75.0%)이지만, 신규 fresh v6 대응은 12/24(50.0%)로 분리해 보고했다.

BGE-M3 embedding 기반 semantic safety classifier 프로토타입은 [`report/semantic_safety_classifier_prototype_v1.md`](report/semantic_safety_classifier_prototype_v1.md)에 정리했다. 이 프로토타입은 held-out 문항을 학습/프로토타입 구성에 쓰지 않았고 v6에서 20/24, FP 0/24를 재현했지만, 분류기 아이디어 선택 자체가 v6 결과 이후 이뤄졌을 수 있으므로 retrospective 결과로만 해석한다. 정식 headline은 future work로 남긴다.

## 오류 분석 요약

- Q002: `태초 광휘의 의지`의 가격과 계정 제한은 맞혔지만, 인접 상품인 `태초 소울 1개 상자`의 월 4회/이월 조건이 섞였습니다. 구조화 근거가 있어도 generator가 인접 행 정보를 혼합할 수 있음을 보여줍니다.
- Q016: 답변은 사실상 정답이었지만 자동 factual proxy에서는 실패로 잡혔습니다. token 기반 proxy는 빠른 비교에는 유용하지만 최종 판단에는 수동 rubric이 필요합니다.
## 한계 및 후속 개선

| 한계 | 개선 방향 |
|---|---|
| 표형 정보 혼입 | structured record 우선 규칙 또는 answer template 추가 |
| 자동 proxy 오판 | 수동 채점 확대 또는 LLM-as-judge 추가 |
| BM25 heuristic 영향 | 순수 BM25 점수를 별도 산출해 검색 비교를 더 엄밀하게 검증 |
| reranker 미적용 | BGE-M3 top-k 결과에 cross-encoder reranker 추가 |
| Safety gate 일반화 한계 | v6 12/24를 최종 fresh 결과로 유지하고, semantic classifier는 retrospective prototype으로만 보고 |
| 문서 수 5개 중심 | 더 많은 패치노트, 이벤트, 가이드 문서로 확장 |
| 고정된 offline benchmark | 패치노트 갱신 주기에 맞춰 질문/정답을 자동 갱신하는 dynamic refreshed evaluation set으로 확장 |
| 운영 로그 미연동 | 질문, 검색 chunk, 답변, latency, safety decision, user feedback을 추적하는 observability layer 추가 |

후속 확장은 두 방향으로 볼 수 있습니다. 첫째, 현재의 offline benchmark를 패치노트가 바뀔 때마다 새 문서 수집, 중요 변경점 추출, 질문/정답 후보 생성, 재평가까지 이어지는 자동 갱신형 평가셋으로 발전시킬 수 있습니다. 둘째, 실제 서비스 적용 단계에서는 RAGAS/DeepEval/LLM-as-a-Judge 같은 자동 평가 도구를 보조 지표로 붙이고, observability layer를 통해 검색 근거, 답변, 지연시간, safety 판단, 사용자 피드백을 기록해 offline 평가와 online 로그를 연결할 수 있습니다.

## 결론

이 프로젝트는 던파 공식 문서를 기반으로 게임 도메인 LLM 평가 과정을 작게 구현한 작업입니다. RAG는 baseline 대비 문서 기반 질문 성능을 크게 개선했고, BGE-M3는 BM25 heuristic보다 top-1 근거 회수 성능이 높았습니다. 추가 요소별 비교 실험에서는 `qwen3:4b-instruct-2507-q4_K_M`이 기존 `qwen3:4b`보다 답변 형식, meta reasoning 억제, 평균 응답 시간에서 더 안정적임을 확인했습니다. 최종 제출용 조합은 factual proxy 단독 최고값이 아니라, 검색 근거성, 답변 형식, 표형 정보 보완을 함께 고려한 균형 조합입니다.
