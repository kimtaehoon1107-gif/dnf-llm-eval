# 2026-07-04 research review handoff (Claude)

작성일: 2026-07-04
브랜치: `codex/v2026-06-results`
작성자: Claude (main conversation, not a separate agent)
목적: Codex를 포함한 다른 실행자가 오늘 한 작업을 검증/이어갈 수 있도록 기록한다. 아직 커밋되지 않았다.

**갱신 안내**: 이 handoff는 최초 작성 후 사람(추정: Codex 쪽 리뷰)이 4가지 표현/라벨 오류를 지적했고, 전부 반영해 본문을 직접 고쳤다(취소선 대신 인라인 정정 표시를 씀). 무엇을 왜 고쳤는지는 맨 아래 "리뷰 후 보정 사항(7/4)" 섹션에 모아뒀다.

## 오늘 진행한 흐름

1. 먼저 `report/research_overview_master.md`, `report/research_summary_and_roadmap.md`(둘 다 7/1 작성, untracked) 두 문서를 7/4 현재 상태로 정리했다. 두 문서가 "앞으로 할 일"로 적어둔 safety held-out v1~v6 프로토콜이 그 사이(7/2~7/3)에 이미 실행 완료됐기 때문이다.
2. 정리하면서 이 프로젝트에서 "바꾸거나 엎으면 좋을 부분" 6가지를 제안했고, 사용자가 전부 순서대로 실행을 요청했다.
3. 6가지를 실제로 실행했다. 그 중 3개(#1, #2, #4)는 실행 과정에서 원래 가설이 틀렸다는 걸 확인하고 방향을 바꿨다 — 아래에 그대로 기록한다.

## 변경/신규 파일 전체 목록 (`git status -s` 기준, 전부 untracked, 커밋 안 함)

```
 M report/README.md
?? eval/auto_extracted_change_records_v1.json
?? eval/heldout_factual_v1_manual_rubric.csv
?? eval/safety_heldout_combined_detail.csv
?? eval/safety_heldout_combined_summary.csv
?? eval/semantic_safety_classifier_detail.csv
?? eval/semantic_safety_classifier_summary.csv
?? report/change_record_extractor_prototype_v1.md
?? report/deepeval_faithfulness_independent_recheck_v1.md
?? report/heldout_factual_v1_manual_rubric_review.md
?? report/heldout_safety_v6_real_world_harm_category_note.md
?? report/research_overview_master.md
?? report/research_summary_and_roadmap.md
?? report/safety_heldout_backward_compat_analysis_v1.md
?? report/semantic_safety_classifier_prototype_v1.md
?? scripts/evaluate_safety_heldout_combined.py
?? scripts/prototype_change_record_extractor.py
?? scripts/prototype_semantic_safety_classifier.py
```

(`report/session_2026_07_04_research_review_handoff.md` 이 파일 자체는 목록 이후에 생성됐다.)

## 1. Safety held-out v1~v6 재검산 — 원래 계획을 스스로 뒤집은 사례

**원래 계획**: v1~v6 held-out 288문항을 전부 합쳐 현재 규칙(`intent_rules_v5`)의 안정적인 recall을 계산한다.

**실행 중 발견한 문제**: `scripts/safety_intent.py`와 커밋 히스토리를 대조해보니 v2~v5의 held-out 결과가 각각 다음 규칙(v3/v4/v5)의 diagnostic·regression 재료로 직접 쓰였다. 즉 v5(현재 규칙)를 v5-heldout에 다시 돌리면 순환 검증이다. "다 합치면 안정적"이라는 원래 아이디어는 methodologically 틀렸다.

**실제로 한 것**: `scripts/evaluate_safety_heldout_combined.py`를 만들어 두 가지를 나눠 계산했다.
- 각 규칙 버전이 실제로 blind였던 조합만 모은 recall: `rules_v2` 58.3%(28/48) → `rules_v3` 50.0%(24/48) → `rules_v4` 37.5%(18/48) → `rules_v5` 50.0%(12/24, 추가할 blind set 없음). 라운드를 거치며 단조 증가하지 않는다.
- 현재 규칙을 과거 세트(v1~v4, v5는 순환이라 제외)에 소급 적용: 75.0%(90/120). 유일한 순수 blind 세트인 v6에서는 여전히 50.0%(12/24).

**결론**: "구식 공격 유지 75% vs 신규 공격 대응 50%"로 나눠 보고하는 게 정확하다. 산출물: `eval/safety_heldout_combined_detail.csv`, `eval/safety_heldout_combined_summary.csv`, `report/safety_heldout_backward_compat_analysis_v1.md`.

**Codex가 검증할 것**: `scripts/evaluate_safety_heldout_combined.py`의 `CIRCULAR_VERSION_FOR_CURRENT_RULES = "v5"` 판단이 맞는지(즉 rules_v5가 정말 v5-heldout의 diagnostic에서 나왔는지) 커밋 로그로 재확인.

## 2. `real_world_harm_self_harm_threats` 카테고리(0/4) — 가설을 두 번 수정

**원래 가설(1차, 폐기)**: "자해 의사를 밝히는 사용자에게는 차단이 아니라 위기 상담 리소스 안내가 필요한데 그게 안 돼서 0/4"라고 추측했다.

**실제 문항(`questions/heldout_safety_v6.csv`의 HSV6-A021~A024) 확인 결과**: 전부 제3자를 향한 협박·괴롭힘·자해 조장 문구 작성이나 현실 위해 장치 제작 요청이었다. 1차 가설은 틀렸다 — 명확한 차단이 맞는 케이스였다.

**진짜 원인**: `report/heldout_safety_v3_attack_type_recall_taxonomy_v2.csv` 등을 확인하니 이 카테고리는 v1~v5의 taxonomy에 아예 없었다. v6 preregistration(`report/heldout_safety_v6_preregistration.md`)에서 처음 도입한 6종 taxonomy의 일부다. 즉 "6라운드 동안 못 고침"이 아니라 "이 카테고리를 겨냥한 rule 자체가 없었음"이 정확한 설명이다.

**의도적으로 지금 안 고침**: v6는 사전 선언된 최종 검증이라, 방금 본 문항(A021~A024) 문구를 보고 규칙을 추가하면 그 자체가 test-informed 오염이다. 그래서 `scripts/safety_intent.py`는 건드리지 않았다. 다음 라운드(v7)의 사전등록 스코프로만 문서에 적어뒀다.

산출물: `report/heldout_safety_v6_real_world_harm_category_note.md`.

**Codex가 검증할 것**: 이 판단(지금 패치 안 함)에 동의하는지. 동의한다면 v7을 열 때 이 문서의 "권장: 다음 라운드(v7) 스코프로 명시" 섹션을 그대로 사전등록에 반영하면 된다.

## 3. DeepEval faithfulness fail 6건 독립 재검증

원래 판정(`report/deepeval_compact_evidence_calibration_v2026_06.md`)은 6건 전부를 자기 판단으로 "judge 오류"로 분류했었다. 그 판정을 보지 않고 `eval/rag_v2026_06_hybrid_structured_fix_instruct_answers.csv`와 `eval/deepeval_rag_v2026_06_structured_fix_compact_top3_faithfulness_judge.csv`를 직접 대조했다.

결과: 5/6(Q012, Q016, Q017, Q019, Q020)은 독립적으로도 동의한다 — 그 중 4건은 judge의 `reason` 텍스트 자체가 "모순 없음/score 1.00"이라고 적어놓고 기록된 `score`는 0~0.5인, DeepEval 도구 자체의 내적 불일치였다(사람이 봐도 재현 가능한 수준). Q003 하나만 "judge 오류"로 완전히 단정하지 않고 경계 사례로 남겼다.

산출물: `report/deepeval_faithfulness_independent_recheck_v1.md`. 새 CSV는 만들지 않고 기존 CSV만 대조했다.

**Codex가 검증할 것**: Q003(빛의 서약 확정 획득 조건절 누락 관련)에 대한 판단에 동의하는지 — 이건 진짜로 애매하다.

## 4. Factual held-out v1(25문항) 수동 rubric 채점

`eval/ablation_v2026_06_heldout_full_completeness_answers.csv`(5개 구조화 조건 중 대표 1개, 전부 23/25로 동률이라 대표성 있음)를 `eval/evaluation_rubric.md` 기준으로 25문항 전부 채점했다.

- HF023, HF024: 기존 자동 proxy fail과 일치 확정 (gold의 조건절을 답변이 누락).
- **HF004(신규 발견)**: gold는 "캐릭터별 필터" + "무기 타입/레어리티 필터" 둘 다 요구하는데 모델은 후자만 답함. 자동 proxy는 token recall 통과 처리해서 이 completeness 결함을 못 잡았다.
- HF025: 모델 답변에 evidence 문장엔 없는 "신실한 소코르스"라는 단어가 있어 환각 의심했으나, 원본 문서(`data/processed_md/DOC-02_5_20...md` 372행)를 직접 대조해 정식 명칭임을 확인, 무혐의 처리.

산출물: `eval/heldout_factual_v1_manual_rubric.csv`, `report/heldout_factual_v1_manual_rubric_review.md`.

## 5. Semantic safety classifier 프로토타입 (오늘 가장 성과가 큰 항목)

`scripts/prototype_semantic_safety_classifier.py`: 파이프라인에 이미 쓰는 `BAAI/bge-m3` 임베딩으로, dev 세트에서만 뽑은 프로토타입(공격 60개: `adversarial_questions.csv`+`adversarial_paraphrase_questions.csv`+`adversarial_stealth_questions.csv`+`safety_intent_attack_expansion.csv`, 정상 72개: `safety_overrefusal_questions.csv`+`safety_intent_benign_expansion.csv`+`benchmark_questions.csv`)만으로 1-NN 분류기를 만들었다. **held-out(v1~v6) 텍스트는 프로토타입 구축에 전혀 안 썼다.**

**(7/4 표현 보정)** 처음엔 이걸 "v1~v6 전부가 여전히 순수 blind 세트"라고 썼는데 과장이었다. 데이터 누출은 없지만, 분류기를 만들기로 한 선택 자체와 `real_world_harm` breakdown을 강조한 것 자체가 이미 v6에서 규칙이 50.0%·해당 카테고리 0/4였다는 걸 안 뒤에 이뤄졌을 수 있다 — 이건 아이디어 선택 단계의 정보 누출이다. 그래서 정확한 표현은 **"held-out 문항을 프로토타입 구성에 쓰지 않은 retrospective evaluation"**이고, 정식 blind headline은 이 분류기를 v7 사전등록에 올린 뒤에만 주장한다. 상세: `report/semantic_safety_classifier_prototype_v1.md`의 "이 결과를 순수 blind라고 부르면 안 되는 이유" 섹션.

결과(v6 기준, retrospective): attack recall 20/24(83.3%), benign FP 0/24 — 6라운드 튜닝한 `intent_rules_v5`(12/24, 50.0%)를 상회했다. 특히 규칙이 0/4였던 `real_world_harm_self_harm_threats`를 임베딩은 3/4까지 잡았다(도메인 규칙 하나도 안 만들었는데도). 이 관찰도 위와 같은 caveat가 적용된다.

한계도 같이 적어뒀다: v2~v4에서 benign FP 1~2건 발생, 설명 가능성이 규칙 기반보다 떨어짐, 아직 자체 사전등록/fresh blind 검증(v7)을 안 거친 프로토타입.

산출물: `eval/semantic_safety_classifier_detail.csv`, `eval/semantic_safety_classifier_summary.csv`, `report/semantic_safety_classifier_prototype_v1.md`.

**Codex가 검증할 것(중요)**: 이 결과가 재현되는지 `scripts/prototype_semantic_safety_classifier.py`를 다시 돌려서 확인 권장. `BAAI/bge-m3` 로딩은 이미 로컬에 캐시돼 있어 실행에 1분 이내 걸렸다(첫 실행이면 더 걸릴 수 있음).

## 6. 자동 change-record 추출기 프로토타입

`scripts/prototype_change_record_extractor.py`: 원본 patch note markdown(`data/snapshots/2026-06-official-updates/processed_md/`, 8개 문서)을 직접 열어보니 변경점이 3가지 패턴(화살표 `A → B`, 서술형 `~가 추가/제거됩니다`, "변경 전/변경 후" 표가 markdown 변환 중 깨진 형태)으로 섞여 있었다. 정규식 3종으로 추출해 hand-authored 5건(`data/snapshots/2026-06-official-updates/structured/change_records.json`)과 비교했다.

- 2/5 완전 자동 복원(화살표·서술형 패턴).
- 1/5 부분 복원(표 패턴, markdown 강조로 값이 여러 줄로 쪼개짐).
- 2/5 실패(대시 없는 서술문 1건, 중첩 대괄호 표 1건).
- 추가 후보 35개를 찾았다. **(7/4 정정)** 그 중 가격 변경("초월의 의지 50개 → 25개")을 처음엔 "hand-authored set에 아예 없던 발견"이라고 썼는데 틀렸다 — `data/snapshots/2026-06-official-updates/structured/shop_items.json`의 `DNF-2927810-SHOP-02`에 이미 있었다. `change_records.json`(5건, 패치노트 스킬/시스템용 스키마)에는 없지만 `shop_items.json`(상점 가격용 스키마)에는 있었던 것 — extractor가 두 스키마를 구분 못 하고 섞어서 쏟아낸 결과다. 몬스터 개명·아바타명 오탈자 수정 등은 어느 스키마에도 없는 진짜 신규 후보로 남는다.

산출물: `eval/auto_extracted_change_records_v1.json`, `report/change_record_extractor_prototype_v1.md`.

**Codex가 검증할 것**: `eval/auto_extracted_change_records_v1.json`의 35개 후보 중 (a) `change_records.json`용인지 (b) `shop_items.json`용인지 (c) 둘 다에 없는 진짜 신규인지 스키마별로 분류하고, 실제로 QA에 쓸 만한 신규 항목만 사람이 골라 추가할지 결정.

## 반영한 문서

- `report/research_overview_master.md`: 3장에 3-9(factual v1 ablation)/3-10(safety v1~v6)/3-11(재검산) 섹션 추가, 4장 성적표에 held-out 실측값 병기, 5장 오염 진단에 "검증 완료" 갱신, 7장 로드맵 1·2·5번 상태 갱신, 8장 산출물 지도에 오늘 만든 8개 문서 추가.
- `report/research_summary_and_roadmap.md`: 1장 표에 ⑨~⑯ 행 추가, 2장 성적표/오염진단/라벨링 상태 갱신.
- `report/README.md`: "제출용 핵심 문서"에 `research_overview_master.md`와 `safety_eval_final_report_v6.md` 추가, "세부 실험 문서"에 오늘 만든 문서 8개 + 기존에 누락돼 있던 `safety_eval_process_summary_for_main_project.md`/`research_summary_and_roadmap.md` 추가.

## 검증 (이 handoff 작성 직전 실행)

```
python scripts\smoke_check.py        -> [DONE] smoke checks passed
python -m py_compile scripts\evaluate_safety_heldout_combined.py scripts\prototype_semantic_safety_classifier.py scripts\prototype_change_record_extractor.py   -> OK
```

`final_closing_review.md`, `final_portfolio_report.md`, `application_summary.md`, `README.md`의 headline 표(20/20, 50/50, 24/24)는 아직 갱신하지 않았다 — 이번 세션은 "새 진단·프로토타입 생성"에 집중했고, 최종 제출 문서 표 반영은 다음 단계다.

## 지금 상태

- 아무것도 커밋하지 않았다. 위 "변경/신규 파일 전체 목록"이 전부 working tree에만 있다.
- 아무 것도 `scripts/safety_intent.py`, `data/.../change_records.json` 같은 프로덕션 파일을 수정하지 않았다 — 전부 진단/프로토타입 스크립트와 report/eval 산출물만 추가했다.

## 다음 추천 순서

1. 이 handoff와 6개 report를 Codex가 검증(특히 5번 semantic classifier 재현, 2번 real_world_harm 판단 동의 여부).
2. 동의하면 `final_closing_review.md`/`final_portfolio_report.md`/`application_summary.md`/`README.md`의 headline 표에 held-out 실측값(factual 23/25, safety backward-compat 75% vs 신규 50%)을 병기.
3. v7 라운드를 열 때 이 문서의 2, 5번 섹션을 사전등록에 반영(real_world_harm 카테고리 추가, semantic classifier 정식 후보 등록).
4. 브랜치 push는 여전히 대기 상태.

## 리뷰 후 보정 사항 (7/4)

이 handoff와 관련 report를 사람이 리뷰하고 4가지를 지적했다. 전부 동의하고 본문에 직접 반영했다(위 1, 4, 5, 6번 섹션 참고). 무엇이 왜 틀렸었는지 요약:

1. **semantic classifier를 "순수 blind"라고 부른 것이 과장이었다.** held-out 텍스트를 프로토타입에 안 쓴 건 맞지만, 분류기 아이디어 선택과 `real_world_harm` 강조 자체가 이미 v6 결과를 본 뒤 이뤄졌을 수 있다(아이디어 선택 단계의 정보 누출). `report/semantic_safety_classifier_prototype_v1.md`, `research_overview_master.md`, `research_summary_and_roadmap.md`, `report/README.md`를 전부 "retrospective evaluation, headline은 v7 이후"로 하향 수정했다.
2. **`combined_blind_excl_circular_v5`라는 스코프 이름이 부정확했다.** v5만 순환인 건 맞지만 현재 규칙은 v2~v4 진단도 누적 반영한 결과라 v1~v4도 "순수 blind"는 아니다. `scripts/evaluate_safety_heldout_combined.py`에서 스코프 이름을 `backward_compat_excl_circular_v5`로 바꾸고 `eval/safety_heldout_combined_summary.csv`를 재생성했다(수치는 동일, 라벨만 정확해짐).
3. **"보이드 소울 가격 변경이 hand-authored set에 아예 없었다"는 주장이 틀렸다.** `data/snapshots/2026-06-official-updates/structured/shop_items.json`의 `DNF-2927810-SHOP-02`에 이미 있었다(확인 완료). `change_records.json`에는 없지만 `shop_items.json`에는 있다는 걸로 정정했고, extractor의 진짜 발견은 "두 스키마를 구분 못 하고 후보를 섞어서 낸다"는 한계로 재정의했다. `report/change_record_extractor_prototype_v1.md`와 두 master 문서를 고쳤다.
4. **HF023/HF024의 `numeric_error_gate=FAIL` 라벨이 부정확했다.** 루브릭상 이 gate는 수치가 틀렸을 때 쓰는 것이고, 두 문항은 숫자가 틀린 게 아니라 조건절/변경 근거를 누락한 completeness 문제였다. `eval/heldout_factual_v1_manual_rubric.csv`에서 두 행의 `numeric_error_gate`를 PASS로 정정하고 completeness 점수로만 반영하도록 note를 고쳤다. 전체 verdict(`fail`)는 그대로다 — 감점 항목만 바로잡았다.

이 4가지 모두 실행 로직이나 원본 수치 자체를 바꾼 게 아니라 **보고 표현/라벨의 정확도**를 고친 것이다. `eval/safety_heldout_combined_summary.csv`만 재생성했고 값은 이전과 동일하다.
