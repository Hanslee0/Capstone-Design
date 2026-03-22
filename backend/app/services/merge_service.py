from typing import Any, Dict, List

from app.services.derived_fields import build_derived_fields


def flatten_schema_fields(schema: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    groups = schema.get("groups", {})

    field_map: Dict[str, Dict[str, Any]] = {}

    collected_fields = groups.get("collected_fields", {})
    auto_fields = collected_fields.get("auto", {})
    semi_auto_fields = collected_fields.get("semi_auto", {})
    manual_fields = groups.get("manual_context_fields", {})
    derived_fields = groups.get("derived_fields", {})

    field_map.update(auto_fields)
    field_map.update(semi_auto_fields)
    field_map.update(manual_fields)
    field_map.update(derived_fields)

    return field_map


def validate_required_fields(
    schema: Dict[str, Any],
    merged_data: Dict[str, Any],
) -> List[str]:
    field_map = flatten_schema_fields(schema)
    missing_fields: List[str] = []

    for field_name, meta in field_map.items():
        if meta.get("required") is True and merged_data.get(field_name) is None:
            missing_fields.append(field_name)

    return missing_fields


def merge_inputs(
    schema: Dict[str, Any],
    aws_data: Dict[str, Any],
    policy_data: Dict[str, Any],
) -> Dict[str, Any]:
    merged_data: Dict[str, Any] = {}

    merged_data.update(aws_data)
    merged_data.update(policy_data)

    derived = build_derived_fields(merged_data)
    merged_data.update(derived)

    missing_fields = validate_required_fields(schema, merged_data)
    if missing_fields:
        raise ValueError(
            f"Required fields missing after merge: {', '.join(missing_fields)}"
        )

    return merged_data