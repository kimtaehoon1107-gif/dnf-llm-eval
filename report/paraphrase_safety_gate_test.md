# Paraphrase Safety Gate Test

작성일: 2026-06-01

## 1. 목적

기존 safety gate는 문자열 기반 규칙으로 동작한다. 따라서 원래 공격 문항의 핵심 단어를 바꾸면 차단 성능이 떨어질 수 있다. 이를 확인하기 위해 기존 adversarial 질문 10개의 의도는 유지하되 표현을 바꾼 paraphrase 공격 세트를 추가했다.

## 2. 추가 데이터

| 파일 | 설명 |
|---|---|
| `questions/adversarial_paraphrase_questions.csv` | 기존 공격 의도를 다른 표현으로 바꾼 10문항 |
| `eval/rag_local_llm_adversarial_paraphrase_safety_gate.csv` | 개선 전 safety gate dry-run 결과 |
| `eval/rag_local_llm_adversarial_paraphrase_answers.csv` | 개선 전 end-to-end generator 답변 결과 |
| `eval/rag_local_llm_adversarial_paraphrase_safety_gate_v2.csv` | 복합 조건 규칙 추가 후 safety gate dry-run 결과 |

## 3. 실험 결과

| 설정 | 차단 수 | 해석 |
|---|---:|---|
| 기존 safety gate + paraphrase set | 0 / 10 | exact keyword 중심 규칙이라 표현이 바뀐 공격을 차단하지 못함 |
| 기존 safety gate 통과 후 generator | 9 / 10 거절 | 프롬프트 규칙이 대부분 방어했지만 1문항에서 문서 근거를 잘못 끌어와 답변 생성 |
| 개선 safety gate v2 + paraphrase set | 10 / 10 | 복합 조건 규칙 추가 후 paraphrase 공격 차단 |
| 개선 safety gate v2 + 기존 adversarial set | 10 / 10 | 기존 공격 세트 차단 성능 유지 |

## 4. 개선 내용

기존 방식은 단일 문자열 포함 여부만 확인했다.

```text
질문에 "시스템 프롬프트" 포함 → prompt_leakage
질문에 "매크로" 포함 → automation_abuse
```

개선 후에는 여러 단서가 함께 등장할 때 차단하는 복합 조건 규칙을 추가했다.

```text
"기본 안내문" + "보여" → prompt_leakage
"사람이 안 눌러도" + "반복 처리" → automation_abuse
"게임 밖" + "돈으로" → real_money_trade
"근거가 부족" + "말하지 말고" → hallucination_induction
```

이 방식은 단일 키워드보다 paraphrase에 조금 더 강하고, `추천`처럼 정상 질문에도 자주 나오는 단어를 단독 차단하지 않아 오탐을 줄일 수 있다.

## 5. 한계

이번 개선은 여전히 규칙 기반 1차 필터다. 실험 세트의 paraphrase를 반영해 성능이 좋아졌지만, 완전히 새로운 우회 표현에는 약할 수 있다. 실제 서비스 수준으로 가려면 다음 보완이 필요하다.

| 한계 | 후속 개선 |
|---|---|
| 규칙 기반이라 표현 다양성에 취약 | paraphrase 공격 세트 지속 확장 |
| 정상 질문 오탐 가능성 | benign safety regression set 추가 |
| 의미적 공격 탐지 한계 | lightweight classifier 또는 LLM-as-judge 보조 |
| 차단 이유 품질 검증 부족 | blocked_category별 수동 검토 |

## 6. 결론

Paraphrase safety test는 기존 safety gate의 약점을 드러냈고, 복합 조건 규칙을 추가해 0/10에서 10/10으로 개선했다. 다만 이 결과는 규칙 기반 테스트 세트에 대한 개선이므로, 최종 보고서에서는 safety gate를 완성된 방어 체계가 아니라 `규칙 기반 1차 필터 + 지속적인 red-team 데이터 확장 대상`으로 설명하는 것이 적절하다.
