# Report Reading Guide

이 폴더에는 최종 제출용 보고서와 실험 과정에서 만든 세부 분석 문서가 들어 있습니다. 초기 계획서와 오래된 중간 결과는 `archive/`에 보관했습니다. 처음 보는 사람은 아래 순서대로 읽는 것이 가장 안전합니다.

## 1. 제출용 핵심 문서

| 순서 | 파일 | 용도 |
|---:|---|---|
| 1 | `final_closing_review.md` | 제출 전 최종 상태, 핵심 수치, 남은 한계를 짧게 확인 |
| 2 | `final_portfolio_report.md` | 전체 프로젝트의 문제 정의, 실험 설계, 결과, 한계를 통합 설명 |
| 3 | `ablation_study_report.md` | BGE-M3 고정 후 모델/톤/구조화 데이터 효과를 분리한 추가 실험 |
| 4 | `application_summary.md` | 지원서와 면접에서 바로 말할 수 있는 요약문 |
| 5 | `model_selection_and_benchmark_rationale.md` | Qwen3, BGE-M3, RAG 평가 지표를 선택한 이유 |
| 6 | `references.md` | RAG 평가, 검색 모델, safety 설계 참고문헌 |

## 2. 세부 실험 문서

| 파일 | 내용 |
|---|---|
| `retriever_comparison_report.md` | BM25 heuristic과 BGE-M3 검색 성능 비교 |
| `answer_retriever_comparison_report.md` | 검색기별 답변 품질 proxy 비교 |
| `ablation_study_report.md` | BGE-M3를 고정하고 생성 설정을 단계적으로 바꾼 변수 통제 실험 |
| `benchmark_questions_v2026_06_design.md` | 2026-06 staged corpus 질문셋 설계와 BM25/BGE-M3/hybrid/rerank 후속 실행 결과 |
| `deepeval_adapter_notes.md` | 2026-06 RAG 답변 CSV를 DeepEval RAG test case JSONL로 변환한 어댑터 설명 |
| `deepeval_faithfulness_manual_review.md` | DeepEval faithfulness fail 7건을 실제 생성 오류와 judge 오류로 분리한 수동 리뷰 |
| `deepeval_compact_evidence_calibration_v2026_06.md` | Structured fix 이후 compact evidence로 DeepEval faithfulness judge를 재보정한 결과 |
| `structured_fix_iteration_v2026_06.md` | DeepEval 수동 리뷰 후 structured 근거와 답변 완전성을 보강해 2026-06 factual proxy 20/20을 만든 재실행 결과 |
| `representative_manual_scoring.md` | 대표 문항을 사람이 읽을 수 있게 수동 채점한 진단 문서 |
| `structured_data_and_safety_gate_update.md` | 상점표 구조화 데이터와 safety gate 추가 내용 |
| `paraphrase_safety_gate_test.md` | 단순 키워드 우회 공격에 대한 보강 실험 |
| `stealth_safety_gate_test.md` | 직접 키워드를 피한 held-out 우회 공격 실험 |
| `safety_design_rationale.md` | rule-based safety gate를 선택한 이유와 한계 |
| `safety_intent_e2e_gate_test.md` | intent safety gate를 실제 RAG 생성 경로에서 end-to-end 실행한 결과 |
| `session_2026_07_01_structured_deepeval_safety_handoff.md` | 2026-07-01 structured fix, DeepEval compact calibration, intent safety e2e 진행 요약 |
| `service_tone_guideline.md` | 서비스 답변 톤과 few-shot 예시 설계 |
| `baseline_and_ablation_design.md` | baseline, RAG, structured data ablation 설계 |

## 3. 중간 산출물

아래 문서들은 프로젝트 진행 중 만든 계획서 또는 중간 결과입니다. 최종 결론을 확인할 때는 위의 제출용 핵심 문서를 먼저 보는 것이 좋습니다.

| 파일 | 성격 |
|---|---|
| `archive/project_direction_report.md` | 초기 프로젝트 방향 설계 |
| `archive/local_llm_experiment_plan.md` | 로컬 LLM 실험 계획 |
| `archive/initial_sample_eval_report.md` | 초기 5개 샘플 평가 결과 |
| `archive/full_eval_report.md` | 초기 전체 평가 보고 |
| `archive/rag_eval_report.md` | RAG 도입 직후 평가 보고 |
| `archive/bge_m3_retrieval_smoke_test.md` | BGE-M3 검색 smoke test |
| `archive/next_improvement_plan.md` | 후속 개선 아이디어 |
| `archive/adversarial_safety_evaluation_plan.md` | 공격 질문 세트 설계 계획 |
| `archive/document_summary.md` | 수집 문서 요약 |
| `archive/evaluation_methodology_research.md` | 평가 방법론 조사 |
| `archive/interview_pitch.md` | 면접 설명 초안 |

## 주의

일부 중간 산출물에는 최종 instruct 모델 적용 전의 결과가 포함되어 있습니다. 최종 판단은 `final_closing_review.md`, `final_portfolio_report.md`, `application_summary.md`를 기준으로 보면 됩니다.
