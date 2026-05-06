from typing import Any, Dict, List, Tuple

from app.core.constants import FIELD_LABELS_KO


def humanize_field_name(field: str | None) -> str:
    if field is None:
        return "미지정 필드"

    safe_field = str(field)
    return FIELD_LABELS_KO.get(safe_field, safe_field.replace("_", " "))


def format_value(value: Any) -> str:
    if value is True:
        return "예"
    if value is False:
        return "아니오"
    if value is None:
        return "미확인"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def extract_binary_condition(
    condition: Dict[str, Any],
    operator: str,
) -> Tuple[str | None, Any]:
    """
    기존 정책팩 형식:
        {"field": "foo", "eq": true}

    destination pack에서 사용한 축약 형식:
        {"eq": ["foo", true]}

    두 형식을 모두 지원한다.
    """
    raw_value = condition.get(operator)
    field = condition.get("field")

    if (
        field is None
        and isinstance(raw_value, list)
        and len(raw_value) == 2
        and isinstance(raw_value[0], str)
    ):
        return raw_value[0], raw_value[1]

    return field, raw_value


def extract_in_condition(
    condition: Dict[str, Any],
) -> Tuple[str | None, List[Any]]:
    """
    기존 형식:
        {"field": "foo", "in": ["a", "b"]}

    축약 형식:
        {"in": ["foo", ["a", "b"]]}
    """
    raw_value = condition.get("in")
    field = condition.get("field")

    if (
        field is None
        and isinstance(raw_value, list)
        and len(raw_value) == 2
        and isinstance(raw_value[0], str)
        and isinstance(raw_value[1], list)
    ):
        return raw_value[0], raw_value[1]

    if isinstance(raw_value, list):
        return field, raw_value

    return field, []


def build_leaf_result(
    *,
    field: str | None,
    actual: Any,
    matched: bool,
    expectation: str,
) -> Dict[str, Any]:
    statement = (
        f"{humanize_field_name(field)}이(가) {expectation} 조건을 "
        f"{'충족' if matched else '충족하지 않음'}"
        f" (현재 값: {format_value(actual)})"
    )
    return {
        "matched": matched,
        "facts": [statement] if matched else [],
        "unmet_facts": [] if matched else [statement],
    }


def evaluate_condition_with_trace(
    condition: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    if not condition:
        return {
            "matched": True,
            "facts": ["추가 조건이 없어 기본적으로 적용됩니다."],
            "unmet_facts": [],
        }

    if "all" in condition:
        sub_results = [
            evaluate_condition_with_trace(sub, context)
            for sub in condition["all"]
        ]
        matched = all(result["matched"] for result in sub_results)
        facts: List[str] = []
        unmet_facts: List[str] = []

        for result in sub_results:
            facts.extend(result["facts"])
            unmet_facts.extend(result["unmet_facts"])

        return {
            "matched": matched,
            "facts": facts if matched else [],
            "unmet_facts": unmet_facts if not matched else [],
        }

    if "any" in condition:
        sub_results = [
            evaluate_condition_with_trace(sub, context)
            for sub in condition["any"]
        ]
        matched_results = [result for result in sub_results if result["matched"]]
        matched = len(matched_results) > 0

        if matched:
            facts: List[str] = []
            for result in matched_results:
                facts.extend(result["facts"])
            return {
                "matched": True,
                "facts": facts,
                "unmet_facts": [],
            }

        unmet_facts: List[str] = []
        for result in sub_results:
            unmet_facts.extend(result["unmet_facts"])
        return {
            "matched": False,
            "facts": [],
            "unmet_facts": unmet_facts,
        }

    if "not" in condition:
        sub_result = evaluate_condition_with_trace(condition["not"], context)
        matched = not sub_result["matched"]
        statement = "하위 조건이 충족되지 않아 부정 조건이 적용됩니다."

        return {
            "matched": matched,
            "facts": [statement] if matched else [],
            "unmet_facts": [] if matched else [statement],
        }

    if "eq" in condition:
        field, expected = extract_binary_condition(condition, "eq")
        actual = context.get(field)

        return build_leaf_result(
            field=field,
            actual=actual,
            matched=actual == expected,
            expectation=f"{format_value(expected)}",
        )

    if "neq" in condition:
        field, expected = extract_binary_condition(condition, "neq")
        actual = context.get(field)

        return build_leaf_result(
            field=field,
            actual=actual,
            matched=actual != expected,
            expectation=f"{format_value(expected)}가 아님",
        )

    if "in" in condition:
        field, allowed_values = extract_in_condition(condition)
        actual = context.get(field)

        allowed_text = ", ".join(format_value(item) for item in allowed_values)

        return build_leaf_result(
            field=field,
            actual=actual,
            matched=actual in allowed_values,
            expectation=f"[{allowed_text}] 중 하나",
        )

    field = condition.get("field")
    actual = context.get(field)

    if condition.get("not_null") is True:
        return build_leaf_result(
            field=field,
            actual=actual,
            matched=actual is not None,
            expectation="값이 존재함",
        )

    if condition.get("is_null") is True:
        return build_leaf_result(
            field=field,
            actual=actual,
            matched=actual is None,
            expectation="값이 비어 있음",
        )

    if condition.get("truthy") is True:
        return build_leaf_result(
            field=field,
            actual=actual,
            matched=bool(actual) is True,
            expectation="참 상태",
        )

    if condition.get("falsy") is True:
        return build_leaf_result(
            field=field,
            actual=actual,
            matched=bool(actual) is False,
            expectation="거짓 상태",
        )

    raise ValueError(f"Unsupported condition format: {condition}")


def evaluate_condition(condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
    return evaluate_condition_with_trace(condition, context)["matched"]