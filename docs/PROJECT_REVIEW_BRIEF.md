# DNF LLM Evaluation Project Review Brief

이 문서는 프로젝트를 처음 보는 리뷰어가 10분 안에 전체 흐름과 감사 포인트를 이해하도록 만든 한 장 요약입니다. 핵심 메시지는 “높은 점수를 만든 프로젝트”가 아니라 “그 점수가 믿을 만한지 검증하고, 오염 가능성을 라벨링한 평가 포트폴리오”입니다.

## 1. 무엇을 했나

던전앤파이터 공식 업데이트 문서를 수집하고, 실제 유저가 물어볼 법한 문서 기반 질문과 OOD/공격 질문을 구성했습니다. 이후 로컬 LLM 답변 품질을 `검색`, `근거 구성`, `생성 모델`, `구조화 데이터`, `safety gate`, `평가 루브릭`으로 나눠 비교했습니다.

주요 파이프라인은 다음과 같습니다.

1. 공식 문서 수집 및 Markdown/metadata 정리
2. benchmark 질문, gold answer, evidence 구성
3. Non-RAG baseline과 RAG 비교
4. BM25 heuristic과 BGE-M3 검색기 비교
5. Qwen3 기본 모델과 instruct variant 비교
6. 구조화 record, held-out ablation, diagnostic probe 분리
7. safety gate v1~v6 평가와 최종 fresh 결과 보고

## 2. 핵심 결과

| 영역 | 결과 | 해석 |
|---|---:|---|
| End-to-end 문서 QA | 11.27 -> 18.86 / 21 | RAG가 긴 패치노트 질문에서 baseline보다 안정적 |
| Retrieval | BGE-M3 top-1 hit 21 / 22 | BM25 heuristic 19 / 22보다 근거 회수 우수 |
| Generator format | 9 / 22 -> 22 / 22 | `qwen3:4b-instruct-2507-q4_K_M`이 영어 추론/meta 발화를 줄임 |
| 2026-06 dev structured fix | 20 / 20 | 실패 분석 뒤 record/rule을 보강한 dev/test-informed 결과 |
| Factual blind held-out | 23 / 25 | 모든 ablation 조건 동률. record가 held-out 0/25 발동 |
| Structured record probe | 24 / 35 -> 30 / 35 -> 32 / 35 | record가 실제 발동하면 구조화 데이터가 도움. 단, held-out 일반화 근거는 아님 |
| Safety fresh v6 | 12 / 24, FP 0 / 24 | regression 50/50 대신 사전 선언한 fresh 결과를 최종 safety headline으로 사용 |
| Semantic safety prototype | v6 20 / 24, FP 0 / 24 | retrospective prototype. 정식 headline은 v7 사전등록 이후 |

## 3. 꼭 조심해서 읽을 부분

`2026-06 structured fix 20/20`은 좋은 결과지만 held-out 일반화 성능으로 주장하지 않습니다. 동일 문항 실패 분석을 바탕으로 record와 rule을 보강한 뒤 재측정했기 때문입니다. 이후 blind held-out 25문항을 freeze했고, structured record는 dev 9/20 문항에는 발동했지만 held-out에서는 0/25 문항에 발동했습니다.

`structured record probe 32/35`도 새 held-out이 아닙니다. 이 실험의 목적은 “record가 실제로 발동하는 조건에서는 structured data가 답변 품질에 도움이 되는가?”를 확인하는 diagnostic입니다.

Safety도 같은 원칙을 적용했습니다. intent gate는 dev/regression 100문항에서 50/50을 통과했지만, 최종 성능 headline은 fresh v6의 12/24, FP 0/24로 낮춰 보고합니다. semantic classifier 20/24는 가능성을 보여준 retrospective prototype이지 최종 성능 주장이 아닙니다.

## 4. 읽는 순서

| 순서 | 파일 | 이유 |
|---:|---|---|
| 1 | `README.md` | 전체 스냅샷과 주의 문구 |
| 2 | `report/final_closing_review.md` | 제출 전 최종 결론 |
| 3 | `report/final_portfolio_report.md` | 전체 실험 과정 |
| 4 | `report/heldout_factual_ablation_v1.md` | dev 20/20과 held-out 23/25 감사 |
| 5 | `report/structured_record_probe_v1.md` | record 발동 조건 diagnostic |
| 6 | `report/safety_eval_final_report_v6.md` | final safety fresh v6 |
| 7 | `report/safety_eval_process_summary_for_main_project.md` | safety v1~v6 과정 추적 |
| 8 | `report/session_2026_07_04_research_review_handoff.md` | 7/4 보정 사항과 후속 연구 후보 |

## 5. 최종 포지션

이 프로젝트의 강점은 모델 성능 숫자 하나가 아니라 평가 설계입니다. 특히 freeze, manifest, held-out, ablation, manual rubric, retrospective 라벨링을 통해 “좋아 보이는 숫자”와 “믿고 주장할 수 있는 숫자”를 분리했습니다.

이번 마무리 범위에서는 v7 새 실험을 진행하지 않습니다. 다음 업그레이드는 모델/규칙을 더 고치는 것이 아니라, 현재 결과의 전달력과 감사 가능성을 높이는 문서 정리입니다.
