# Semantic Safety Classifier Prototype (BGE-M3 embedding, v1)

작성일: 2026-07-04 (2026-07-04 표현 보정: retrospective 프레이밍으로 하향)

**핵심 한 줄**: Semantic classifier는 held-out 문항을 학습/프로토타입 구성에 쓰지 않은 **retrospective prototype**으로서 v6에서 20/24(83.3%), FP 0/24를 재현했지만, **정식 headline은 v7 fresh preregistered 검증 뒤로 둔다.**

## 배경

로드맵 5번 항목("intent gate 의미 기반화")은 v6까지 규칙 기반 gate를 held-out에서 측정하는 것만 완료하고, "공격 프로토타입 임베딩 유사도나 소형 분류기로 실제로 옮기는 작업"은 미착수로 남아 있었다. 이 문서는 그 최소 프로토타입을 만들고 같은 held-out 세트에서 규칙 기반 gate와 정면 비교한 결과다.

## 방법

- 임베딩: 파이프라인에 이미 쓰는 `BAAI/bge-m3`(`scripts/run_rag_local_llm_eval.py`의 `load_bge_m3_model`/`encode_bge_dense` 재사용).
- 분류기: 학습이나 threshold 튜닝 없는 가장 단순한 1-nearest-neighbor 방식. 공격 프로토타입 집합과 정상 프로토타입 집합을 각각 임베딩하고, 새 질문을 두 집합 중 가장 가까운(cosine 최대) 쪽으로 분류한다.
- 공격 프로토타입(60개): `adversarial_questions.csv`, `adversarial_paraphrase_questions.csv`, `adversarial_stealth_questions.csv`, `safety_intent_attack_expansion.csv` — 전부 **dev 세트**다.
- 정상 프로토타입(72개): `safety_overrefusal_questions.csv`, `safety_intent_benign_expansion.csv`, `benchmark_questions.csv` — 전부 **dev 세트**다.
- **held-out(v1~v6)은 프로토타입 구축에 전혀 쓰지 않았다.** 이 점이 규칙 기반 gate와의 결정적 차이다 — 규칙은 v2~v5의 diagnostic으로 계속 다시 만들어졌지만, 이 임베딩 분류기는 처음부터 dev 세트만 보고 고정됐다.
- 스크립트: `scripts/prototype_semantic_safety_classifier.py`. 산출물: `eval/semantic_safety_classifier_detail.csv`, `eval/semantic_safety_classifier_summary.csv`.

## 결과: held-out별 recall/FP

| held-out | attack recall | benign FP |
|---|---:|---:|
| v1 | 24/24 (100.0%) | 0/24 (0.0%) |
| v2 | 20/24 (83.3%) | 1/24 (4.2%) |
| v3 | 21/24 (87.5%) | 2/24 (8.3%) |
| v4 | 21/24 (87.5%) | 1/24 (4.2%) |
| v5 | 14/24 (58.3%) | 0/24 (0.0%) |
| v6 | 20/24 (83.3%) | 0/24 (0.0%) |
| **합산(v1~v6)** | **120/144 (83.3%)** | **4/144 (2.8%)** |

## 핵심 비교: v6(규칙 기반 gate에게 유일하게 순수했던 blind 세트) 기준 규칙 vs 임베딩

| gate | attack recall (v6) | benign FP (v6) |
|---|---:|---:|
| `intent_rules_v5` (6라운드 튜닝) | 12/24 (50.0%) | 0/24 (0.0%) |
| 임베딩 1-NN 프로토타입 (튜닝 0라운드) | **20/24 (83.3%)** | 0/24 (0.0%) |

카테고리별로 보면 차이가 더 뚜렷하다.

| attack type | `intent_rules_v5` | 임베딩 프로토타입 |
|---|---:|---:|
| credential_phishing_privacy_harassment | 1/4 | 3/4 |
| game_exploit_and_reward_abuse | 4/4 | 3/4 |
| automation_botting_and_client_tampering | 3/4 | 4/4 |
| malware_prompt_injection_and_cyber_abuse | 1/4 | 3/4 |
| fraud_marketplace_and_economy_abuse | 3/4 | 4/4 |
| real_world_harm_self_harm_threats | **0/4** | **3/4** |

가장 중요한 차이는 `real_world_harm_self_harm_threats`다. `heldout_safety_v6_real_world_harm_category_note.md`에서 진단한 대로, 규칙 기반 gate는 이 카테고리에 대응하는 rule 자체가 없어서 0/4였다. 반면 임베딩 분류기는 게임 도메인 규칙을 하나도 만들지 않았는데도 이 카테고리에서 3/4를 잡았다 — "게임 오브젝트를 현실 위해 장치로 만드는 방법"류 문장이 attack 프로토타입(꼭 같은 카테고리가 아니어도 다른 유해 요청들)과 의미적으로 가깝기 때문이다.

## 이 결과를 "순수 blind"라고 부르면 안 되는 이유

`safety_heldout_backward_compat_analysis_v1.md`에서 지적했듯, 규칙 기반 gate는 v2~v5 각 라운드의 진단을 규칙에 직접 반영했기 때문에 v1~v5는 최종 규칙(`rules_v5`)에게 더 이상 blind 세트가 아니다. 이 임베딩 프로토타입은 held-out 문항의 **텍스트 자체는 프로토타입 구축에 쓰지 않았다** — 그 점에서 규칙 기반과는 분명히 다르다.

다만 이걸 "순수 blind 대규모 추정치"라고 부르는 건 과장이다. 이유는 데이터 누출이 아니라 **아이디어 선택 단계의 정보 누출**이다.

- 이 분류기를 만들기로 한 시점에 이미 `intent_rules_v5`가 v6에서 50.0%에 그쳤고 `real_world_harm_self_harm_threats`에서 0/4였다는 사실을 알고 있었다.
- 즉 "임베딩 유사도 방식을 시도해보자"는 선택 자체, 그리고 결과를 본 뒤 `real_world_harm` 카테고리 breakdown을 확인해 강조한 것 자체가, 이미 알고 있던 규칙의 약점을 겨냥한 사후 설계일 수 있다.
- held-out 문항을 프로토타입 벡터에 직접 섞지 않았다는 것과, 이 방법론 전체가 v6 결과를 보기 전부터 계획된 완전한 사전등록 실험이었다는 것은 다른 이야기다. 후자는 아니다.

그래서 이 결과는 held-out 문항을 학습/프로토타입 구성에 쓰지 않은 **retrospective evaluation**이라고 부르는 게 정확하다. "규칙 기반 쪽에서는 만들 수 없었던 대규모 blind 추정치"라는 표현은 쓰지 않는다. 결과 자체(83.3%, FP 0%)는 매우 유망하지만, 완전한 blind headline이 되려면 **이 분류기 아이디어를 v7 사전등록에 먼저 명시하고, v7이 나온 뒤 그 결과로만 판단해야 한다.**

한 가지 실질적 장점은 남는다 — 접근 방식의 재현성 측면에서, 규칙은 매 라운드 다시 튜닝해야 하고 그때마다 이전 held-out이 오염되지만, 임베딩 프로토타입은 프로토타입 집합만 고정하면 새 held-out이 나올 때마다 (텍스트 자체의 데이터 누출 없이) 계속 재평가할 수 있다는 점이다. 이건 방법론적 장점이지 이번 수치 자체가 완전한 blind라는 뜻은 아니다.

## 한계 (프로토타입 단계, 프로덕션 대체 아님)

- 프로토타입 132개는 여전히 손으로 고른 예시일 뿐이며, threshold/margin 조정이나 교차검증 없이 가장 단순한 1-NN만 썼다.
- benign FP가 v2~v4에서 1~2건씩 나온다 — 규칙 기반보다 recall은 훨씬 높지만 FP가 0이 아닌 라운드가 있다(과탐지 성향). v6에서는 0/24였지만 표본이 작아 안정적이라 단정하기 어렵다.
- 설명 가능성이 떨어진다. 규칙 기반은 "어떤 키워드/카테고리에 걸렸는지" 사람이 바로 읽을 수 있는 반면, 이 분류기는 "가장 가까운 프로토타입 문장과 cosine 유사도"만 준다 — 어떤 프로토타입에 걸렸는지는 로그로 남길 수 있지만 규칙만큼 직관적이지 않다.
- 매 요청마다 임베딩 계산이 필요해 규칙 기반보다 느리고 리소스를 더 쓴다(다만 이미 검색에 BGE-M3를 쓰고 있어 추가 모델 로드 비용은 없다).
- 이 결과 하나로 "임베딩이 최종 해법"이라고 단정하지 않는다. 프로젝트가 계속 지켜온 원칙대로, 이 프로토타입도 자체 전용 사전등록 + 새 fresh blind set(v7 이후)으로 다시 검증해야 headline으로 쓸 수 있다.

## 결론 및 권장

- 최소 프로토타입이 v6에서 20/24(83.3%), FP 0/24를 재현해 규칙 기반 6라운드 튜닝 결과(50.0%)를 상회했다. 이 수치는 유망하지만 **retrospective prototype 결과이지 정식 blind headline이 아니다** — 정식 headline은 이 분류기를 v7 사전등록에 올리고 fresh blind 결과가 나온 뒤에 판단한다.
- 특히 규칙 기반이 구조적으로 대응 자체가 없었던 `real_world_harm_self_harm_threats`(0/4)를 임베딩은 도메인 규칙 없이 3/4까지 잡았다 — 다만 이 관찰도 v6 결과를 본 뒤 강조한 것이므로 같은 caveat가 적용된다.
- 다음 라운드(v7) 스코프에 이 임베딩 분류기를 정식 후보로 등록하고, benign FP 성향과 설명 가능성 트레이드오프를 fresh blind set에서 함께 측정하는 것을 권장한다.

## 산출물

- `scripts/prototype_semantic_safety_classifier.py`
- `eval/semantic_safety_classifier_detail.csv`
- `eval/semantic_safety_classifier_summary.csv`
