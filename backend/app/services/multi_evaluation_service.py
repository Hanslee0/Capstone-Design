from typing import Any, Dict, List

from app.services.applicable_pack_service import build_applicable_pack_plan
from app.services.evaluation_service import evaluate_rules
from app.services.pack_loader import load_pack
from app.services.request_merge_service import build_merged_input_from_request


def _evaluate_single_pack(
    application: Dict[str, str],
    aws_data: Dict[str, Any],
    policy_data: Dict[str, Any],
    raise_on_error: bool,
) -> Dict[str, Any]:
    pack_id = application["pack_id"]

    try:
        merged_input = build_merged_input_from_request(
            aws_data=aws_data,
            policy_data=policy_data,
            pack_id=pack_id,
            schema_file_name=None,
        )

        pack_data = load_pack(pack_id=pack_id)

        result = evaluate_rules(
            merged_input=merged_input,
            pack_data=pack_data,
        )

        return {
            "pack_id": pack_id,
            "country": application["country"],
            "role": application["role"],
            "reason": application["reason"],
            "final_decision": result["final_decision"],
            "result": result,
            "error": None,
        }

    except Exception as exc:
        if raise_on_error:
            raise

        return {
            "pack_id": pack_id,
            "country": application["country"],
            "role": application["role"],
            "reason": application["reason"],
            "final_decision": None,
            "result": None,
            "error": str(exc),
        }


def _build_reference_warnings(reference_results: List[Dict[str, Any]]) -> List[str]:
    warnings: List[str] = []

    for item in reference_results:
        if item.get("error"):
            warnings.append(
                f"{item['pack_id']} 참고 검토 중 오류가 발생했습니다: {item['error']}"
            )
            continue

        decision = item.get("final_decision")

        if decision in ["deny", "manual_review"]:
            warnings.append(
                f"{item['pack_id']} 참고 검토 결과 {decision} 판정이 나왔습니다. "
                "주 적용 법령 기준 최종판정과 별도로 추가 확인이 필요합니다."
            )

    return warnings


def evaluate_multiple_packs(
    origin_country: str,
    destination_country: str,
    aws_data: Dict[str, Any],
    policy_data: Dict[str, Any],
    include_destination_reference: bool = True,
    extra_pack_ids: List[str] | None = None,
    merged_cloud_input: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    plan = build_applicable_pack_plan(
        origin_country=origin_country,
        destination_country=destination_country,
        include_destination_reference=include_destination_reference,
        extra_pack_ids=extra_pack_ids or [],
    )

    primary_pack_id = plan["primary_pack_id"]

    primary_application = next(
        item for item in plan["applications"]
        if item["pack_id"] == primary_pack_id and item["role"] == "primary_export_law"
    )

    reference_applications = [
        item for item in plan["applications"]
        if item is not primary_application
    ]

    primary_result = _evaluate_single_pack(
        application=primary_application,
        aws_data=aws_data,
        policy_data=policy_data,
        raise_on_error=True,
    )

    reference_results = [
        _evaluate_single_pack(
            application=application,
            aws_data=aws_data,
            policy_data=policy_data,
            raise_on_error=False,
        )
        for application in reference_applications
    ]

    overall_decision = primary_result["final_decision"]
    overall_warnings = _build_reference_warnings(reference_results)

    overall_summary = (
        f"출발국가({origin_country}) 기준 주 적용 정책팩 "
        f"{primary_pack_id}의 판정을 최종 판정으로 사용합니다. "
        f"도착국가({destination_country}) 관련 정책팩은 참고 검토 결과로 표시됩니다."
    )

    results_by_pack = [primary_result] + reference_results

    return {
        "origin_country": origin_country,
        "destination_country": destination_country,
        "primary_pack_id": primary_pack_id,
        "reference_pack_ids": plan["reference_pack_ids"],
        "overall_decision": overall_decision,
        "overall_summary": overall_summary,
        "overall_warnings": overall_warnings,
        "primary_result": primary_result,
        "reference_results": reference_results,
        "results_by_pack": results_by_pack,
        "merged_cloud_input": merged_cloud_input or {},
    }