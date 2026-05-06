from fastapi import APIRouter, HTTPException

from app.schemas.multi_evaluation import (
    ApplicablePacksRequest,
    ApplicablePacksResponse,
    MultiEvaluateRequest,
    MultiEvaluationResponse,
)
from app.services.applicable_pack_service import build_applicable_pack_plan
from app.services.cloud.cloud_normalizer import normalize_cloud_input
from app.services.cloud.mock_cloud_discovery_service import discover_mock_cloud
from app.services.multi_evaluation_service import evaluate_multiple_packs

router = APIRouter(prefix="/api/v1", tags=["multi-evaluate"])

def apply_destination_defaults(policy_data: dict) -> dict:
    defaults = {
        "processing_purpose_defined": True,
        "processing_legal_basis": "contract",
        "processing_legal_basis_available": True,
        "data_minimized": True,

        "contains_sensitive_data": False,
        "special_category_condition_met": True,
        "explicit_consent_for_sensitive_data": True,

        "privacy_policy_available": True,
        "transfer_notice_provided": True,
        "cross_border_notice_provided": True,
        "data_subject_rights_request_ready": True,

        "retention_period_defined": True,
        "retention_policy_available": True,

        "recipient_contract_available": True,
        "processor_contract_available": True,
        "dpa_available": True,

        "security_measures_available": True,
        "encryption_at_rest": True,
        "encryption_in_transit": True,
        "access_control_in_place": True,

        "incident_response_in_place": True,
        "risk_assessment_completed": True,
        "appropriate_safeguards_available": True,
    }

    cleaned = dict(policy_data or {})

    for key, value in defaults.items():
        if key not in cleaned or cleaned.get(key) is None:
            cleaned[key] = value

    return cleaned


@router.post("/applicable-packs", response_model=ApplicablePacksResponse)
def get_applicable_packs(payload: ApplicablePacksRequest):
    try:
        return build_applicable_pack_plan(
            origin_country=payload.origin_country,
            destination_country=payload.destination_country,
            include_destination_reference=payload.include_destination_reference,
            extra_pack_ids=payload.extra_pack_ids,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/evaluate-multi", response_model=MultiEvaluationResponse)
def evaluate_multi(payload: MultiEvaluateRequest):
    try:
        aws_data = dict(payload.aws_data)
        merged_cloud_input = {}

        if payload.use_mock_cloud:
            if not payload.cloud_provider:
                raise ValueError(
                    "cloud_provider is required when use_mock_cloud is true."
                )

            raw_cloud_data = discover_mock_cloud(
                cloud_provider=payload.cloud_provider,
                destination_country=payload.destination_country,
                resource=payload.cloud_resource,
            )

            merged_cloud_input = normalize_cloud_input(
                raw_data=raw_cloud_data,
                destination_country=payload.destination_country,
            )

            aws_data.update(merged_cloud_input)

        cleaned_policy_data = apply_destination_defaults(payload.policy_data)

        return evaluate_multiple_packs(
            origin_country=payload.origin_country,
            destination_country=payload.destination_country,
            aws_data=aws_data,
            policy_data=cleaned_policy_data,
            include_destination_reference=payload.include_destination_reference,
            extra_pack_ids=payload.extra_pack_ids,
            merged_cloud_input=merged_cloud_input,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e