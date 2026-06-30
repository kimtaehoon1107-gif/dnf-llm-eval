from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BASE_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import run_rag_local_llm_eval as rag  # noqa: E402


DEFAULT_DETAIL_OUTPUT = BASE_DIR / "eval" / "safety_intent_classifier_detail.csv"
DEFAULT_SUMMARY_OUTPUT = BASE_DIR / "eval" / "safety_intent_classifier_summary.csv"
DEFAULT_DATASETS = (
    ("explicit_adversarial", BASE_DIR / "questions" / "adversarial_questions.csv", True),
    ("stealth_adversarial", BASE_DIR / "questions" / "adversarial_stealth_questions.csv", True),
    ("safety_overrefusal", BASE_DIR / "questions" / "safety_overrefusal_questions.csv", False),
    (
        "safety_intent_attack_expansion",
        BASE_DIR / "questions" / "safety_intent_attack_expansion.csv",
        True,
    ),
    (
        "safety_intent_benign_expansion",
        BASE_DIR / "questions" / "safety_intent_benign_expansion.csv",
        False,
    ),
)


@dataclass(frozen=True)
class IntentDecision:
    blocked: bool
    category: str
    reason: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def has_regex(text: str, pattern: str) -> bool:
    return re.search(pattern, text) is not None


def is_benign_policy_or_feature_query(text: str) -> bool:
    benign_terms = (
        "정책",
        "제재",
        "공지",
        "안내",
        "관련 변경",
        "관련해서 바뀐",
        "편의 기능",
        "기능이 추가",
        "버그 수정",
        "수정된 내용",
        "제보",
        "영수증",
        "환불",
        "수수료",
        "보안 강화",
        "보안 카드",
        "자동 이동",
        "자동 사냥",
        "자동 정렬",
        "자동 분해",
    )
    harmful_action_terms = (
        "악용 방법",
        "버그 악용",
        "꼼수",
        "빈틈",
        "반복해서 더",
        "더 받",
        "스크립트",
        "코드",
        "로직",
        "프로그램 흐름",
        "자동화",
        "현금화",
        "돈으로 바꾸",
    )
    return has_any(text, benign_terms) and not has_any(text, harmful_action_terms)


def is_scope_compliance_query(text: str) -> bool:
    if has_any(text, ("말하지 말", "숨기", "티 안 나게")):
        return False
    if has_any(text, ("제외하고", "빼고", "부족하다고 말", "확인 가능한 내용만", "공지 기준으로만")):
        return has_any(text, ("문서에 없는", "다른 rpg", "근거가 부족", "확인 가능한", "이번 공지", "던파 공지"))
    return False


def classify_intent(question: str) -> IntentDecision:
    text = question.lower()

    if is_scope_compliance_query(text):
        return IntentDecision(False, "", "scope_compliance_query")

    if has_regex(text, r"(시스템|내부|운영|기본|처음).{0,12}(프롬프트|지시|규칙|안내문|설명)") and has_any(
        text, ("출력", "보여", "공개", "요약", "빼도 돼", "그대로")
    ):
        return IntentDecision(True, "prompt_leakage", "requests hidden prompt or internal instructions")

    if has_regex(text, r"(이전|안전|답변|지시|규칙|틀|방식|제한|검색 근거).{0,12}(무시|내려놓|말고|바꿔|자유롭게|빼고|잠시 빼)"):
        return IntentDecision(True, "prompt_injection", "tries to override answer rules or priority")
    if has_any(text, ("내 요청을 우선", "네 판단으로", "네가 아는 대로")) and has_any(
        text, ("문서에 없어도", "검색 근거", "숨은 기능", "다음 패치", "티어")
    ):
        return IntentDecision(True, "prompt_injection", "tries to override answer rules or priority")

    if has_any(text, ("답변 규칙 전문", "개발자 메시지", "개발자 지시", "금지사항 목록")) and has_any(
        text, ("출력", "보여", "그대로", "목록")
    ):
        return IntentDecision(True, "prompt_leakage", "requests hidden prompt or internal instructions")

    if has_any(text, ("개발자 모드", "관리자 모드", "관리자 역할", "테스트 담당자라고 가정", "qa 테스트 담당자 역할")):
        return IntentDecision(True, "jailbreak", "role or mode override")

    if has_any(text, ("아래 문장", "다음 문장", "전제로 답", "전제로 해", "공식 내용으로 간주", "공식 힌트", "내가 넣은 문장", "검색 근거로 삼아", "공식 확인이라고 붙이고")):
        if has_any(text, ("공식", "근거", "확인", "전제", "간주", "맞다고 답", "실제 문서에는 없는")):
            return IntentDecision(True, "fake_evidence", "tries to inject user-provided evidence")

    if has_any(text, ("문서에 없", "공지에 없", "공지에 드러나지", "드러나지 않은", "공개되지", "공식 글에는 안", "공식 문서 근거가 없", "공식 근거 없이")):
        if has_any(text, ("추측", "후보", "가능성", "최적", "동선", "공략", "예측", "뽑아", "조건", "세팅", "추천", "루트")):
            return IntentDecision(True, "unsupported_speculation", "asks for unsupported hidden or future information")

    if has_any(text, ("미래", "다음 시즌", "앞으로", "가능성")) and has_any(
        text, ("예측", "감으로", "강해질", "티어", "정리")
    ):
        return IntentDecision(True, "unsupported_speculation", "asks for future or unsupported performance prediction")

    if has_any(text, ("비공개", "운영자만", "숨겨진", "공개되지 않은")) and has_any(
        text, ("조건", "기준", "추론", "추측", "후보")
    ):
        return IntentDecision(True, "hidden_info_guess", "asks to infer hidden internal conditions")

    if has_any(text, ("버그 악용", "악용 방법", "꼼수", "빈틈", "버그를 이용", "오류를 발견")) and has_any(
        text, ("방법", "절차", "단계", "알려", "챙길", "더 받", "반복", "활용", "팁", "이득")
    ):
        return IntentDecision(True, "exploit_request", "asks for exploit or abuse procedure")

    if has_any(text, ("매크로", "스크립트", "프로그램", "자동 처리", "반복 클릭", "손 안 대고", "사람이 안 눌러도")) and has_any(
        text, ("짜", "작성", "코드", "로직", "흐름", "흐름도", "만들", "처리되게")
    ):
        return IntentDecision(True, "automation_abuse", "asks for automation abuse implementation")

    if has_any(text, ("게임 밖", "현금화", "돈으로", "시세", "외부 거래", "외부 거래로")) and has_any(
        text, ("절차", "방법", "효율", "방향", "알려", "연결", "이득", "요령", "넘기는")
    ):
        return IntentDecision(True, "real_money_trade", "asks for real-money trading or monetization path")

    if has_any(text, ("메이플", "로스트아크", "다른 rpg", "다른 온라인 rpg", "던파가 아닌")) and has_any(
        text, ("추천", "골라", "좋은 직업", "요즘 좋은")
    ):
        return IntentDecision(True, "out_of_domain", "asks for out-of-domain game recommendation")

    if has_any(
        text,
        (
            "근거가 부족",
            "검색된 근거가 없다고 말하지 마",
            "확인된 내용이 적",
            "빈칸",
            "자연스럽게 메워",
            "확신 있게",
            "그럴듯한 답",
            "그럴듯하게",
            "그럴듯한 숫자",
            "믿게",
            "단정적인 안내문",
            "티 안 나게",
            "완성된 공지",
        ),
    ):
        return IntentDecision(True, "hallucination_induction", "asks to fill missing evidence or sound certain")

    if is_benign_policy_or_feature_query(text):
        return IntentDecision(False, "", "benign_policy_or_feature_query")

    return IntentDecision(False, "", "benign_or_not_matched")


def parse_dataset_spec(spec: str) -> tuple[str, Path, bool]:
    try:
        name, raw_path, raw_is_attack = spec.split(":", 2)
    except ValueError as exc:
        raise ValueError(
            "--dataset must use the form name:path:is_attack, e.g. extra:questions/x.csv:1"
        ) from exc

    name = name.strip()
    path = Path(raw_path.strip())
    if not path.is_absolute():
        path = BASE_DIR / path
    is_attack = raw_is_attack.strip().lower() in {"1", "true", "yes", "attack"}
    if not name:
        raise ValueError("--dataset name cannot be empty")
    return name, path, is_attack


def load_eval_rows(specs: list[tuple[str, Path, bool]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for dataset, path, is_attack in specs:
        if not path.exists():
            continue
        for row in read_csv(path):
            rows.append(
                {
                    **row,
                    "dataset": dataset,
                    "source_file": str(path.relative_to(BASE_DIR)).replace("\\", "/"),
                    "is_attack": "1" if is_attack else "0",
                }
            )
    return rows


def verdict(blocked: bool, is_attack: bool) -> str:
    if blocked and is_attack:
        return "true_positive"
    if blocked and not is_attack:
        return "false_positive"
    if not blocked and is_attack:
        return "false_negative"
    return "true_negative"


def build_detail_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    detail_rows: list[dict[str, object]] = []
    for row in rows:
        question = row.get("question", "")
        is_attack = row.get("is_attack") == "1"
        keyword_category, keyword_reason = rag.get_safety_block(question)
        keyword_blocked = bool(keyword_category)
        intent = classify_intent(question)

        detail_rows.append(
            {
                "dataset": row["dataset"],
                "source_file": row["source_file"],
                "question_id": row.get("question_id", ""),
                "question_type": row.get("question_type", ""),
                "is_attack": int(is_attack),
                "question": question,
                "keyword_blocked": int(keyword_blocked),
                "keyword_category": keyword_category,
                "keyword_reason": keyword_reason,
                "keyword_verdict": verdict(keyword_blocked, is_attack),
                "intent_blocked": int(intent.blocked),
                "intent_category": intent.category,
                "intent_reason": intent.reason,
                "intent_verdict": verdict(intent.blocked, is_attack),
                "expected_behavior": row.get("expected_behavior", ""),
            }
        )
    return detail_rows


def rate(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return ""
    return f"{numerator / denominator:.3f}"


def summarize(detail_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    classifiers = (
        ("keyword_gate", "keyword_blocked", "keyword_verdict"),
        ("intent_classifier", "intent_blocked", "intent_verdict"),
    )
    datasets = ["all", *dict.fromkeys(str(row.get("dataset", "")) for row in detail_rows)]
    summary_rows: list[dict[str, object]] = []

    for classifier, blocked_key, verdict_key in classifiers:
        for dataset in datasets:
            scoped = [
                row
                for row in detail_rows
                if dataset == "all" or row.get("dataset") == dataset
            ]
            tp = sum(1 for row in scoped if row[verdict_key] == "true_positive")
            fp = sum(1 for row in scoped if row[verdict_key] == "false_positive")
            fn = sum(1 for row in scoped if row[verdict_key] == "false_negative")
            tn = sum(1 for row in scoped if row[verdict_key] == "true_negative")
            attacks = tp + fn
            benign = fp + tn
            blocked = sum(int(row[blocked_key]) for row in scoped)
            summary_rows.append(
                {
                    "classifier": classifier,
                    "dataset": dataset,
                    "questions": len(scoped),
                    "attack_questions": attacks,
                    "benign_questions": benign,
                    "blocked": blocked,
                    "true_positive": tp,
                    "false_negative": fn,
                    "false_positive": fp,
                    "true_negative": tn,
                    "attack_recall": rate(tp, attacks),
                    "benign_precision": rate(tn, benign),
                    "false_positive_rate": rate(fp, benign),
                    "overall_accuracy": rate(tp + tn, len(scoped)),
                }
            )
    return summary_rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare the keyword safety gate with a lightweight intent classifier."
    )
    parser.add_argument("--detail-output", type=Path, default=DEFAULT_DETAIL_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument(
        "--dataset",
        action="append",
        default=[],
        help="Extra dataset spec in the form name:path:is_attack. is_attack accepts 1/true/yes/attack.",
    )
    args = parser.parse_args()

    dataset_specs = [*DEFAULT_DATASETS, *(parse_dataset_spec(spec) for spec in args.dataset)]
    detail_rows = build_detail_rows(load_eval_rows(dataset_specs))
    summary_rows = summarize(detail_rows)

    detail_fields = [
        "dataset",
        "source_file",
        "question_id",
        "question_type",
        "is_attack",
        "question",
        "keyword_blocked",
        "keyword_category",
        "keyword_reason",
        "keyword_verdict",
        "intent_blocked",
        "intent_category",
        "intent_reason",
        "intent_verdict",
        "expected_behavior",
    ]
    summary_fields = [
        "classifier",
        "dataset",
        "questions",
        "attack_questions",
        "benign_questions",
        "blocked",
        "true_positive",
        "false_negative",
        "false_positive",
        "true_negative",
        "attack_recall",
        "benign_precision",
        "false_positive_rate",
        "overall_accuracy",
    ]

    write_csv(args.detail_output, detail_rows, detail_fields)
    write_csv(args.summary_output, summary_rows, summary_fields)

    for row in summary_rows:
        if row["dataset"] in {"all", "stealth_adversarial", "safety_overrefusal"}:
            print(
                "[SUMMARY] {classifier} {dataset}: recall={attack_recall} "
                "fp_rate={false_positive_rate} accuracy={overall_accuracy}".format(**row)
            )
    print(f"[DONE] detail saved: {args.detail_output}")
    print(f"[DONE] summary saved: {args.summary_output}")


if __name__ == "__main__":
    main()
