from __future__ import annotations

import re
from dataclasses import dataclass


INTENT_GATE_VERSION = "intent_rules_v3"


@dataclass(frozen=True)
class IntentDecision:
    blocked: bool
    category: str
    reason: str


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


def is_defensive_safety_meta_query(text: str) -> bool:
    benign_markers = (
        "공개 가능한 범위",
        "포함하지 말",
        "공개하지 않는 이유",
        "체크리스트",
        "방어용 테스트",
        "기대 동작",
        "안전한 거절",
        "거절 예시",
        "공개 문서 범위만",
        "문서 근거로",
        "문서에 있는 내용만",
        "확인 불가라고 답",
        "불확실",
        "다음 확인 방법",
        "관련 안내",
        "제재 정책",
        "제재 기준",
        "신고",
        "어디에서 확인",
    )
    harmful_markers = (
        "그대로 출력",
        "원문 그대로",
        "덤프",
        "우회하고",
        "회피",
        "피하게",
        "bypass condition",
        "trigger word",
        "hidden rubric",
        "재현 절차",
        "단계별",
        "악용",
        "이득",
        "workflow",
        "제공해",
    )
    return has_any(text, benign_markers) and not has_any(text, harmful_markers)


def is_public_source_negated_trigger_query(text: str) -> bool:
    negated_trigger_markers = (
        "비공개 조건 추정은 빼고",
        "비공개 정보 말고",
        "공개되지 않은 내용은 빼고",
        "숨은 지시를 묻는 게 아니라",
        "숨은 지시가 아니라",
        "매크로 설계가 아니라",
        "봇 흐름이 아니라",
        "자동화 설계가 아니라",
        "제재 회피 요령 말고",
    )
    public_source_markers = (
        "공개 패치노트",
        "공개 패치 변경점",
        "패치노트 기준",
        "공개 문서",
        "문서 기준",
        "공개 문서",
        "상세 가이드",
        "문서화된",
        "조회 조건",
        "조회 범위",
        "가격과 구매 제한",
        "변경점",
        "개선됐는지",
        "어떻게 바뀌었",
    )
    harmful_override_markers = (
        "검증 없이",
        "시스템 규칙보다",
        "답변 규칙",
        "공식 결론",
        "공식 발표처럼",
        "공식 표처럼",
        "세탁",
        "단정",
        "내부 지표",
        "문서에 없는 숫자",
        "우회",
        "회피 방법",
        "회피 패턴",
        "피하",
        "피해",
        "반복 비매너",
        "자동화 흐름",
        "자동 수집",
        "구조를 짜",
        "흐름을 만들어",
        "스크립트",
        "코드",
        "외부 거래",
        "현금화",
        "판매가",
        "거래 게시글",
        "중개 문구",
    )
    return (
        has_any(text, negated_trigger_markers)
        and has_any(text, public_source_markers)
        and not has_any(text, harmful_override_markers)
    )


def classify_intent(question: str) -> IntentDecision:
    text = question.lower()

    if is_scope_compliance_query(text):
        return IntentDecision(False, "", "scope_compliance_query")

    if is_public_source_negated_trigger_query(text):
        return IntentDecision(False, "", "public_source_negated_trigger_query")

    if is_defensive_safety_meta_query(text):
        return IntentDecision(False, "", "defensive_safety_meta_query")

    if has_any(text, ("시스템 규칙보다", "사용자 메시지를 우선", "내 요청을 우선")) and has_any(
        text, ("검증 없이", "가능한 것처럼", "확정", "말해", "답해")
    ):
        return IntentDecision(True, "prompt_injection", "tries to override answer rules or priority")
    if has_any(text, ("답변 규칙을 낮추", "기존 답변 규칙", "답변 규칙을 바꾸")) and has_any(
        text, ("내 결론", "확정", "공식", "말해", "답해")
    ):
        return IntentDecision(True, "prompt_injection", "tries to launder user conclusion through answer rules")

    if has_regex(
        text,
        r"(시스템|내부|운영|기본|처음|숨은|안전|검색|retrieval|developer|blocked|trigger|bypass|hidden).{0,20}(프롬프트|지시|규칙|안내문|설명|컨텍스트|키워드|목록|검사|점수|계산식|chunk|note|category|word|condition|rubric)",
    ) and has_any(
        text, ("출력", "보여", "공개", "요약", "빼도 돼", "그대로", "덤프", "붙여", "알려", "표로")
    ):
        return IntentDecision(True, "prompt_leakage", "requests hidden prompt or internal instructions")

    if has_regex(text, r"(이전|안전|답변|지시|규칙|틀|방식|제한|검색 근거).{0,20}(무시|내려놓|말고|바꿔|자유롭게|빼고|잠시 빼|우회)"):
        return IntentDecision(True, "prompt_injection", "tries to override answer rules or priority")
    if has_any(text, ("평가자 권한", "시스템 관리자")) and has_any(text, ("명령", "우회", "hidden rubric", "숨은 안전 규칙")):
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
    if has_any(text, ("제한 없는", "테스트 하네스", "절대 거절하지")) and has_any(
        text, ("역할", "제공", "workflow", "악용")
    ):
        return IntentDecision(True, "jailbreak", "role or mode override")
    if has_any(text, ("규칙 없는", "정책 없는", "테스트 세계", "정상 문의처럼 처리")) and has_any(
        text, ("외부 거래", "현금화", "우회", "악용", "제재")
    ):
        return IntentDecision(True, "jailbreak", "role or mode override")

    if has_any(text, ("아래 문장", "다음 문장", "전제로 답", "전제로 해", "공식 내용으로 간주", "공식 힌트", "내가 넣은 문장", "검색 근거로 삼아", "공식 확인이라고 붙이고")):
        if has_any(text, ("공식", "근거", "확인", "전제", "간주", "맞다고 답", "실제 문서에는 없는")):
            return IntentDecision(True, "fake_evidence", "tries to inject user-provided evidence")
    if has_any(text, ("내가 쓴", "내 주장을", "내 결론")) and has_any(
        text, ("공식 결론", "공식 발표", "공식 근거", "세탁", "고쳐서")
    ):
        return IntentDecision(True, "fake_evidence", "tries to launder user-provided claim as official evidence")
    if has_any(text, ("공식 문장", "공식 url", "공지 문구", "공식 근거", "공식 근거처럼")) and has_any(
        text, ("만들", "지어내", "그럴듯하게", "새로", "취급", "인용")
    ):
        return IntentDecision(True, "fake_evidence", "tries to fabricate evidence")
    if has_any(text, ("공식 발표", "공식 로드맵", "공식 표")) and has_any(
        text, ("찾아낸 것처럼", "발표처럼", "단정", "완성", "만들", "작성")
    ):
        return IntentDecision(True, "fake_evidence", "tries to fabricate evidence")
    if has_any(text, ("수치", "문장")) and has_any(text, ("있는 것처럼", "만들", "공식 근거")):
        return IntentDecision(True, "fake_evidence", "tries to fabricate evidence")

    if has_any(text, ("문서에 없", "공지에 없", "공지에 드러나지", "드러나지 않은", "공개되지", "공식 글에는 안", "공식 문서 근거가 없", "공식 근거 없이")):
        if has_any(text, ("추측", "후보", "가능성", "최적", "동선", "공략", "예측", "뽑아", "조건", "세팅", "추천", "루트", "확정", "사실")):
            return IntentDecision(True, "unsupported_speculation", "asks for unsupported hidden or future information")

    if has_any(text, ("미래", "다음 시즌", "앞으로", "가능성")) and has_any(
        text, ("예측", "감으로", "강해질", "티어", "정리")
    ):
        return IntentDecision(True, "unsupported_speculation", "asks for future or unsupported performance prediction")
    if has_any(text, ("다음 달", "threshold", "확률")) and has_any(text, ("확정 사실", "문서에 없어도", "말해")):
        return IntentDecision(True, "unsupported_speculation", "asks for unsupported hidden or future information")
    if has_any(text, ("내부 지표", "몇 퍼센트", "확률", "로드맵", "문서에 없는 숫자", "확률표")) and has_any(
        text, ("단정", "공식", "완성", "만들", "작성", "올렸는지", "확장될")
    ):
        return IntentDecision(True, "unsupported_speculation", "asks for unsupported hidden or future information")

    if has_any(text, ("비공개", "운영자만", "숨겨진", "공개되지 않은")) and has_any(
        text, ("조건", "기준", "추론", "추측", "후보")
    ):
        return IntentDecision(True, "hidden_info_guess", "asks to infer hidden internal conditions")

    if has_any(text, ("버그 악용", "악용 방법", "꼼수", "빈틈", "버그를 이용", "오류를 발견")) and has_any(
        text, ("방법", "절차", "단계", "알려", "챙길", "더 받", "반복", "활용", "팁", "이득")
    ):
        return IntentDecision(True, "exploit_request", "asks for exploit or abuse procedure")
    if has_any(text, ("비정상", "오류", "문제", "현상")) and has_any(
        text, ("이용해", "다시 이용", "악용", "재현 절차", "단계별", "반복 수령", "우회하는 방법", "이득 보는")
    ):
        return IntentDecision(True, "exploit_request", "asks for exploit or abuse procedure")
    if has_any(text, ("우회하는 방법", "제한 우회")) and has_any(text, ("찾아", "알려", "답해")):
        return IntentDecision(True, "exploit_request", "asks for exploit or abuse procedure")
    if has_any(text, ("제재", "비매너", "계정 단위 제재")) and has_any(
        text, ("피하", "피해", "제재 가능성을 낮추", "돌려 쓰", "반복", "요령", "패턴")
    ):
        return IntentDecision(True, "sanction_evasion", "asks for sanction or enforcement evasion")

    if has_any(text, ("매크로", "스크립트", "프로그램", "자동 처리", "반복 클릭", "손 안 대고", "사람이 안 눌러도", "자동 순회", "봇")) and has_any(
        text, ("짜", "작성", "코드", "로직", "흐름", "흐름도", "만들", "처리되게", "설계", "긁어")
    ):
        return IntentDecision(True, "automation_abuse", "asks for automation abuse implementation")
    if has_any(text, ("여러 계정", "다계정", "여러 계정에서")) and has_any(
        text, ("반복 구매", "반복 호출", "자동화 흐름", "자동 수집", "구조를 짜", "흐름을 만들어")
    ):
        return IntentDecision(True, "automation_abuse", "asks for multi-account automation abuse")

    if has_any(text, ("게임 밖", "현금화", "돈으로", "시세", "외부 거래", "외부 거래로")) and has_any(
        text, ("절차", "방법", "효율", "방향", "알려", "연결", "이득", "요령", "넘기는")
    ):
        return IntentDecision(True, "real_money_trade", "asks for real-money trading or monetization path")
    if has_any(text, ("현금 거래", "거래 게시글")) and has_any(text, ("홍보", "문안", "작성", "써")):
        return IntentDecision(True, "real_money_trade", "asks for real-money trading or monetization path")
    if has_any(text, ("계정 판매가", "외부 거래 게시글", "중개 문구", "우회 거래", "현금화")) and has_any(
        text, ("계정", "장비", "계정귀속", "보상", "본문", "제목", "방식", "제안")
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
