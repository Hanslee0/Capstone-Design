from typing import Any, Dict

from app.services.merge_service import merge_inputs
from app.services.pack_loader import load_gdpr_pack
from app.services.file_loader import load_json_file
from app.utils.path_helper import get_policy_pack_path


def build_merged_input_from_request(
    aws_data: Dict[str, Any],
    policy_data: Dict[str, Any],
    schema_file_name: str = "input_schema_v2.json",
) -> Dict[str, Any]:
    policy_pack_path = get_policy_pack_path()
    schema = load_json_file(policy_pack_path / schema_file_name)

    return merge_inputs(
        schema=schema,
        aws_data=aws_data,
        policy_data=policy_data,
    )