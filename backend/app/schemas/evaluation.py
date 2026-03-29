from typing import Any, Dict, List

from pydantic import BaseModel


class TriggeredRuleResponse(BaseModel):
    rule_id: str
    article: int
    title: str
    category: str
    priority: int
    decision: str
    risk_score_delta: int
    compliance_score_delta: int
    message: str
    required_actions: List[str]
    references: List[str]


class FinalEvaluationResponse(BaseModel):
    message: str
    final_decision: str
    risk_level: str
    matched_rule_count: int
    base_risk_score: int
    base_compliance_score: int
    total_risk_score: int
    total_compliance_score: int
    legal_basis_articles: List[int]
    required_actions: List[str]
    triggered_rules: List[TriggeredRuleResponse]
    merged_input: Dict[str, Any]