from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.decision import DecisionGrade
from app.schemas.evaluation import FinalEvaluationResponse


class ApplicablePacksRequest(BaseModel):
    origin_country: str = Field(..., description="Data exporting country")
    destination_country: str = Field(..., description="Data importing country")
    include_destination_reference: bool = Field(
        default=True,
        description="Whether to include destination country law as reference review",
    )
    extra_pack_ids: List[str] = Field(
        default_factory=list,
        description="Additional manually selected policy pack ids",
    )


class PackApplicationResponse(BaseModel):
    pack_id: str
    country: str
    role: str
    reason: str


class ApplicablePacksResponse(BaseModel):
    origin_country: str
    destination_country: str
    primary_pack_id: str
    reference_pack_ids: List[str]
    applications: List[PackApplicationResponse]


class MultiEvaluateRequest(BaseModel):
    origin_country: str
    destination_country: str

    aws_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Existing auto/semi-auto cloud input data",
    )
    policy_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Manual legal or business context input data",
    )

    include_destination_reference: bool = True
    extra_pack_ids: List[str] = Field(default_factory=list)

    use_mock_cloud: bool = Field(
        default=False,
        description="Use mock cloud discovery result for demo",
    )
    cloud_provider: Optional[str] = Field(
        default=None,
        description="aws | azure | manual",
    )
    cloud_resource: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional mock cloud resource hint",
    )


class PackEvaluationItem(BaseModel):
    pack_id: str
    country: str
    role: str
    reason: str
    final_decision: Optional[DecisionGrade] = None
    result: Optional[FinalEvaluationResponse] = None
    error: Optional[str] = None


class MultiEvaluationResponse(BaseModel):
    origin_country: str
    destination_country: str

    primary_pack_id: str
    reference_pack_ids: List[str]

    overall_decision: DecisionGrade
    overall_summary: str
    overall_warnings: List[str]

    primary_result: PackEvaluationItem
    reference_results: List[PackEvaluationItem]
    results_by_pack: List[PackEvaluationItem]

    merged_cloud_input: Dict[str, Any] = Field(default_factory=dict)