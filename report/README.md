# Report Reading Guide

이 폴더에는 최종 제출용 보고서와 실험 과정에서 만든 세부 분석 문서가 들어 있습니다. 초기 계획서와 오래된 중간 결과는 `archive/`에 보관했습니다. 처음 보는 사람은 아래 순서대로 읽는 것이 가장 안전합니다.

## 1. 제출용 핵심 문서

| 순서 | 파일 | 용도 |
|---:|---|---|
| 1 | `../docs/PROJECT_REVIEW_BRIEF.md` | 리뷰어/면접관용 1-page 핵심 설명 |
| 2 | `research_overview_master.md` | 전체 연구 과정·현재 성적표·로드맵을 잇는 최상위 색인 (가장 최근 갱신) |
| 3 | `final_closing_review.md` | 제출 전 최종 상태, 핵심 수치, 남은 한계를 짧게 확인 |
| 4 | `final_portfolio_report.md` | 전체 프로젝트의 문제 정의, 실험 설계, 결과, 한계를 통합 설명 |
| 5 | `heldout_factual_ablation_v1.md` | dev 20/20과 blind held-out 23/25, record 0/25 비전이 감사 |
| 6 | `safety_eval_final_report_v6.md` | safety gate held-out v1~v6 개선 라운드 최종 보고서 (intent_rules_v5, v6 12/24) |
| 7 | `structured_record_probe_v1.md` | record가 실제 발동하는 조건에서 structured data가 도움 되는지 진단 |
| 8 | `ablation_study_report.md` | BGE-M3 고정 후 모델/톤/구조화 데이터 효과를 분리한 추가 실험 |
| 9 | `application_summary.md` | 지원서와 면접에서 바로 말할 수 있는 요약문 |
| 10 | `model_selection_and_benchmark_rationale.md` | Qwen3, BGE-M3, RAG 평가 지표를 선택한 이유 |
| 11 | `references.md` | RAG 평가, 검색 모델, safety 설계 참고문헌 |

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
| `heldout_factual_ablation_v1.md` | blind held-out 25문항에서 structured record가 0/25 발동했음을 확인한 감사 실험 |
| `heldout_factual_v1_manual_rubric_review.md` | factual held-out 25문항 수동 rubric 재채점. HF004 completeness 누락 신규 발견, HF025 환각 의심 해소 |
| `structured_record_probe_v1.md` | held-out이 아니라 record 발동 조건에서 structured data 효과를 분리한 diagnostic/probe |
| `change_record_extractor_prototype_v1.md` | 화살표/서술형/표 패턴 자동 change-record 추출기 프로토타입, hand-authored 세트 커버리지 비교 |
| `safety_eval_process_summary_for_main_project.md` | safety gate held-out v1~v6 개선 라운드 전체 과정 요약과 파일 인덱스 |
| `safety_heldout_backward_compat_analysis_v1.md` | safety held-out v1~v6를 단순 합산하지 않고, 구식 공격 유지력(75%)과 신규 공격 대응력(v6, 50%)을 분리 재검산 |
| `heldout_safety_v6_real_world_harm_category_note.md` | v6 real_world_harm 카테고리 0/4의 원인이 규칙 취약이 아니라 taxonomy 신규 도입임을 재진단 |
| `semantic_safety_classifier_prototype_v1.md` | BGE-M3 임베딩 기반 의미 분류기 retrospective 프로토타입, v6에서 규칙 기반 gate(50.0%) 대비 83.3%로 우위 확인(정식 headline은 v7 사전등록 이후) |
| `deepeval_faithfulness_independent_recheck_v1.md` | DeepEval faithfulness fail 6건 자기판정을 독립 재검증(5/6 확정, 1/6 경계 사례) |
| `research_summary_and_roadmap.md` | 연구 요약·현재 목표·held-out 실행 지시문을 담은 보조 색인 |
| `representative_manual_scoring.md` | 대표 문항을 사람이 읽을 수 있게 수동 채점한 진단 문서 |
| `structured_data_and_safety_gate_update.md` | 상점표 구조화 데이터와 safety gate 추가 내용 |
| `paraphrase_safety_gate_test.md` | 단순 키워드 우회 공격에 대한 보강 실험 |
| `stealth_safety_gate_test.md` | 직접 키워드를 피한 held-out 우회 공격 실험 |
| `safety_design_rationale.md` | rule-based safety gate를 선택한 이유와 한계 |
| `safety_intent_e2e_gate_test.md` | intent safety gate를 실제 RAG 생성 경로에서 end-to-end 실행한 결과 |
| `safety_heldout_instruction_v1.md` | safety v6 제작에 쓰인 blind 작성 프로토콜 템플릿 |
| `session_2026_07_01_structured_deepeval_safety_handoff.md` | 2026-07-01 structured fix, DeepEval compact calibration, intent safety e2e 진행 요약 |
| `session_2026_07_04_research_review_handoff.md` | 2026-07-04 Claude가 진행한 6개 재검증/프로토타입 작업 요약, Codex 검증용 handoff |
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
