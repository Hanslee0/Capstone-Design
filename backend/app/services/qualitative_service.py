from typing import Any, Dict, List, Set


RULE_ID_TO_CHECKLIST_KEY = {
    "gdpr-art-9-special-category-review": "special_category_review",
    "gdpr-art-28-processor-guarantees-review": "processor_review",
    "gdpr-art-49-derogation-manual-review": "derogation_review",
    "gdpr-art-32-security-program-review": "security_review",
}

RULE_ID_TO_UNCERTAINTY_FIELD = {
    "gdpr-art-9-special-category-review": "special_category_condition_met",
    "gdpr-art-28-processor-guarantees-review": "processor_sufficient_guarantees",
    "gdpr-art-49-derogation-manual-review": "derogation_used",
    "gdpr-art-32-security-program-review": "incident_response_in_place",
}


def build_review_boundary_summary(pack_data: Dict[str, Any]) -> str:
    templates = pack_data.get("qualitative_review_templates", {})
    boundary_summary = templates.get("boundary_summary", {})

    auto_decidable = boundary_summary.get(
        "auto_decidable",
        "일부 기술적·문서적 요소는 자동 판정 가능합니다.",
    )
    manual_review = boundary_summary.get(
        "manual_review",
        "일부 해석 의존 요소는 수동 검토가 필요합니다.",
    )

    return f"{auto_decidable} {manual_review}"


def collect_triggered_rule_ids(triggered_rules: List[Dict[str, Any]]) -> Set[str]:
    return {rule["rule_id"] for rule in triggered_rules}


def collect_checklist_items(
    pack_data: Dict[str, Any],
    triggered_rules: List[Dict[str, Any]],
) -> List[str]:
    templates = pack_data.get("qualitative_review_templates", {})
    checklist_templates = templates.get("checklist_templates", {})

    checklist: List[str] = []
    seen: Set[str] = set()
    triggered_rule_ids = collect_triggered_rule_ids(triggered_rules)

    for rule_id, checklist_key in RULE_ID_TO_CHECKLIST_KEY.items():
        if rule_id not in triggered_rule_ids:
            continue

        for item in checklist_templates.get(checklist_key, []):
            if item not in seen:
                seen.add(item)
                checklist.append(item)

    return checklist


def collect_uncertainty_flags(
    pack_data: Dict[str, Any],
    triggered_rules: List[Dict[str, Any]],
) -> List[str]:
    templates = pack_data.get("qualitative_review_templates", {})
    uncertainty_map = templates.get("uncertainty_flags", {})

    flags: List[str] = []
    seen: Set[str] = set()
    triggered_rule_ids = collect_triggered_rule_ids(triggered_rules)

    for rule_id, uncertainty_field in RULE_ID_TO_UNCERTAINTY_FIELD.items():
        if rule_id not in triggered_rule_ids:
            continue

        message = uncertainty_map.get(uncertainty_field)
        if message and message not in seen:
            seen.add(message)
            flags.append(message)

    return flags


def build_qualitative_review_hints(
    pack_data: Dict[str, Any],
    triggered_rules: List[Dict[str, Any]],
    final_decision: str,
) -> Dict[str, Any]:
    boundary_summary = build_review_boundary_summary(pack_data)
    checklist = collect_checklist_items(pack_data, triggered_rules)
    uncertainty_flags = collect_uncertainty_flags(pack_data, triggered_rules)

    manual_review_required = (
        final_decision == "manual_review"
        or len(checklist) > 0
        or len(uncertainty_flags) > 0
    )

    return {
        "manual_review_required": manual_review_required,
        "review_boundary_summary": boundary_summary,
        "checklist": checklist,
        "uncertainty_flags": uncertainty_flags,
    }