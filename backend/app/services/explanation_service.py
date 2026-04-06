from typing import Any, Dict, List


DECISION_SUMMARY_MAP = {
    "deny": "현재 입력값 기준으로 해당 처리 또는 이전은 허용되기 어렵습니다.",
    "manual_review": "자동 판정만으로 결론 내리기 어려워 추가 수동 검토가 필요합니다.",
    "allow_with_conditions": "현재 입력값 기준으로 조건부 허용 가능하지만 추가 조치가 필요합니다.",
    "allow": "현재 입력값 기준으로 주요 요건이 충족되어 허용 가능합니다.",
}


def build_summary(
    final_decision: str,
    triggered_rules: List[Dict[str, Any]],
) -> str:
    if triggered_rules:
        highest_priority_rule = triggered_rules[0]
        base_summary = DECISION_SUMMARY_MAP.get(
            final_decision,
            "평가 결과를 확인해 주세요.",
        )
        return f"{base_summary} 핵심 근거는 제{highest_priority_rule['article']}조 관련 규칙입니다."

    return DECISION_SUMMARY_MAP.get(
        final_decision,
        "평가 결과를 확인해 주세요.",
    )


def build_explanation(
    final_decision: str,
    merged_input: Dict[str, Any],
    triggered_rules: List[Dict[str, Any]],
    legal_basis_articles: List[int],
) -> str:
    data_subject_region = merged_input.get("data_subject_region", "UNKNOWN")
    current_region = merged_input.get("current_region", "UNKNOWN")
    target_region = merged_input.get("target_region", "UNKNOWN")
    is_third_country_transfer = merged_input.get("is_third_country_transfer", False)

    rule_messages = [rule["message"] for rule in triggered_rules]
    articles_text = ", ".join([f"제{article}조" for article in legal_basis_articles])

    transfer_text = (
        "제3국 이전에 해당합니다."
        if is_third_country_transfer
        else "제3국 이전에 해당하지 않습니다."
    )

    if rule_messages:
        joined_messages = " ".join(rule_messages)
        return (
            f"본 평가는 {data_subject_region} 정보주체 데이터를 기준으로 "
            f"{current_region}에서 {target_region}로의 처리/배치 상황을 검토했습니다. "
            f"{transfer_text} "
            f"적용된 핵심 조문은 {articles_text}이며, "
            f"주요 판정 근거는 다음과 같습니다: {joined_messages}"
        )

    return (
        f"본 평가는 {data_subject_region} 정보주체 데이터를 기준으로 "
        f"{current_region}에서 {target_region}로의 처리/배치 상황을 검토했습니다. "
        f"{transfer_text} "
        f"특별히 발동한 규칙은 없으며, 현재 입력값 기준으로 {final_decision} 상태입니다."
    )


def build_next_steps(required_actions: List[str]) -> List[str]:
    if not required_actions:
        return ["추가 조치가 필요하지 않으면 현재 설정과 문서 상태를 유지하세요."]

    return required_actions