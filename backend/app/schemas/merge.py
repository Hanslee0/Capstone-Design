from pydantic import BaseModel


class MergeSampleRequest(BaseModel):
    aws_file_name: str = "aws_discovered.sample.json"
    policy_file_name: str = "policy_context.sample.yaml"
    schema_file_name: str = "input_schema_v2.json"


class MergeResponse(BaseModel):
    message: str
    merged_input: dict