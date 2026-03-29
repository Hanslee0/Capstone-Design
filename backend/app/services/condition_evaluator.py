from typing import Any, Dict, List


def evaluate_condition(condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
    if "all" in condition:
        return all(evaluate_condition(sub, context) for sub in condition["all"])

    if "any" in condition:
        return any(evaluate_condition(sub, context) for sub in condition["any"])

    field = condition.get("field")
    value = context.get(field)

    if "eq" in condition:
        return value == condition["eq"]

    if "neq" in condition:
        return value != condition["neq"]

    if "in" in condition:
        allowed_values = condition["in"]
        return value in allowed_values

    raise ValueError(f"Unsupported condition format: {condition}")