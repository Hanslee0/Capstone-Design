from fastapi import APIRouter, HTTPException

from app.schemas.evaluation import FinalEvaluationResponse
from app.schemas.merge import MergeSampleRequest
from app.services.evaluation_service import evaluate_rules
from app.services.file_loader import load_json_file, load_yaml_file
from app.services.merge_service import merge_inputs
from app.services.pack_loader import load_gdpr_pack
from app.utils.path_helper import get_policy_pack_path, get_sample_input_path

router = APIRouter(prefix="/api/v1", tags=["evaluate"])


@router.post("/evaluate-sample", response_model=FinalEvaluationResponse)
def evaluate_sample(payload: MergeSampleRequest):
    try:
        policy_pack_path = get_policy_pack_path()
        sample_input_path = get_sample_input_path()

        schema = load_json_file(policy_pack_path / payload.schema_file_name)
        aws_data = load_json_file(sample_input_path / payload.aws_file_name)
        policy_data = load_yaml_file(sample_input_path / payload.policy_file_name)

        merged_input = merge_inputs(schema, aws_data, policy_data)
        pack_data = load_gdpr_pack()

        return evaluate_rules(merged_input=merged_input, pack_data=pack_data)

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e