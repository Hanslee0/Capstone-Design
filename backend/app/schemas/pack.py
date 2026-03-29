from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class PackSummaryResponse(BaseModel):
    pack_id: str
    pack_name: str
    jurisdiction: str
    version: str
    description: str
    included_articles: List[int]
    rule_count: int


class RuleDetailResponse(BaseModel):
    rule_id: str
    article: int
    title: str
    category: str
    priority: int
    decision: str
    risk_score_delta: int
    compliance_score_delta: int
    when: Dict[str, Any]
    required_evidence: List[str]
    required_actions: List[str]
    message: str
    references: List[str]


class PackDetailResponse(BaseModel):
    pack_id: str
    pack_name: str
    jurisdiction: str
    version: str
    description: str
    source: Dict[str, Any]
    decision_priority: Dict[str, Any]
    scoring_policy: Dict[str, Any]
    rule_count: int
    qualitative_review_templates: Optional[Dict[str, Any]] = None