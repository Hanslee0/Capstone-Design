from typing import Any, Dict, List


def resolve_final_decision(
    triggered_rules: List[Dict[str, Any]],
    decision_order: List[str],
) -> str:
    if not triggered_rules:
        return "allow"

    decisions = [rule["decision"] for rule in triggered_rules]

    for decision in decision_order:
        if decision in decisions:
            return decision

    return "allow"


def resolve_risk_level(total_risk_score: int, score_bands: Dict[str, List[int]]) -> str:
    for level_name, band in score_bands.items():
        min_score, max_score = band
        if min_score <= total_risk_score <= max_score:
            return level_name

    return "unknown"


def collect_legal_basis_articles(triggered_rules: List[Dict[str, Any]]) -> List[int]:
    articles = {rule["article"] for rule in triggered_rules}
    return sorted(articles)


def collect_required_actions(triggered_rules: List[Dict[str, Any]]) -> List[str]:
    seen = set()
    actions: List[str] = []

    for rule in triggered_rules:
        for action in rule.get("required_actions", []):
            if action not in seen:
                seen.add(action)
                actions.append(action)

    return actions