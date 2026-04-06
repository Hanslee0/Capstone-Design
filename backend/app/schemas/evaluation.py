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


class QualitativeReviewHintsResponse(BaseModel):
    manual_review_required: bool
    review_boundary_summary: str
    checklist: List[str]
    uncertainty_flags: List[str]


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
    summary: str
    explanation: str
    next_steps: List[str]
    qualitative_review_hints: QualitativeReviewHintsResponse
    triggered_rules: List[TriggeredRuleResponse]
    merged_input: Dict[str, Any]