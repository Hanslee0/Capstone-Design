from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EvaluateRequest(BaseModel):
    aws_data: Dict[str, Any] = Field(
        ...,
        description="Auto or semi-auto collected cloud input data"
    )
    policy_data: Dict[str, Any] = Field(
        ...,
        description="Manual legal/policy context input data"
    )
    schema_file_name: str = Field(
        default="input_schema_v2.json",
        description="Schema file name to use for validation and merge"
    )
    pack_file_name: str = Field(
        default="gdpr_pack_v2.json",
        description="Policy pack file name to use for evaluation"
    )