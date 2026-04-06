from typing import Any, Dict, List

from app.services.condition_evaluator import evaluate_condition
from app.services.explanation_service import (
    build_explanation,
    build_next_steps,
    build_summary,
)
from app.services.qualitative_service import build_qualitative_review_hints
from app.services.resolution_service import (
    collect_legal_basis_articles,
    collect_required_actions,
    resolve_final_decision,
    resolve_risk_level,
)


def evaluate_rules(
    merged_input: Dict[str, Any],
    pack_data: Dict[str, Any],
) -> Dict[str, Any]:
    scoring_policy = pack_data.get("scoring_policy", {})
    decision_priority = pack_data.get("decision_priority", {})

    base_risk_score = scoring_policy.get("base_risk_score", 0)
    base_compliance_score = scoring_policy.get("base_compliance_score", 0)
    caps = scoring_policy.get("caps", {})

    decision_order = decision_priority.get(
        "order",
        ["deny", "manual_review", "allow_with_conditions", "allow"],
    )
    score_bands = decision_priority.get("score_bands", {})

    triggered_rules: List[Dict[str, Any]] = []
    total_risk_score = base_risk_score
    total_compliance_score = base_compliance_score

    rules = pack_data.get("rules", [])

    for rule in rules:
        when_clause = rule.get("when", {})
        is_matched = evaluate_condition(when_clause, merged_input)

        if is_matched:
            triggered_rules.append(
                {
                    "rule_id": rule["rule_id"],
                    "article": rule["article"],
                    "title": rule["title"],
                    "category": rule["category"],
                    "priority": rule["priority"],
                    "decision": rule["decision"],
                    "risk_score_delta": rule["risk_score_delta"],
                    "compliance_score_delta": rule["compliance_score_delta"],
                    "message": rule["message"],
                    "required_actions": rule["required_actions"],
                    "references": rule["references"],
                }
            )

            total_risk_score += rule["risk_score_delta"]
            total_compliance_score += rule["compliance_score_delta"]

    total_risk_score = max(
        caps.get("min_risk_score", 0),
        min(total_risk_score, caps.get("max_risk_score", 100)),
    )
    total_compliance_score = max(
        caps.get("min_compliance_score", 0),
        min(total_compliance_score, caps.get("max_compliance_score", 100)),
    )

    triggered_rules.sort(key=lambda x: x["priority"], reverse=True)

    final_decision = resolve_final_decision(triggered_rules, decision_order)
    risk_level = resolve_risk_level(total_risk_score, score_bands)
    legal_basis_articles = collect_legal_basis_articles(triggered_rules)
    required_actions = collect_required_actions(triggered_rules)

    summary = build_summary(final_decision, triggered_rules)
    explanation = build_explanation(
        final_decision=final_decision,
        merged_input=merged_input,
        triggered_rules=triggered_rules,
        legal_basis_articles=legal_basis_articles,
    )
    next_steps = build_next_steps(required_actions)

    qualitative_review_hints = build_qualitative_review_hints(
        pack_data=pack_data,
        triggered_rules=triggered_rules,
        final_decision=final_decision,
    )

    return {
        "message": "Rules evaluated, final decision resolved, explanation generated, and qualitative review hints added successfully.",
        "final_decision": final_decision,
        "risk_level": risk_level,
        "matched_rule_count": len(triggered_rules),
        "base_risk_score": base_risk_score,
        "base_compliance_score": base_compliance_score,
        "total_risk_score": total_risk_score,
        "total_compliance_score": total_compliance_score,
        "legal_basis_articles": legal_basis_articles,
        "required_actions": required_actions,
        "summary": summary,
        "explanation": explanation,
        "next_steps": next_steps,
        "qualitative_review_hints": qualitative_review_hints,
        "triggered_rules": triggered_rules,
        "merged_input": merged_input,
    }