from typing import Any, Dict

from app.core.constants import (
    AWS_REGION_TO_COUNTRY,
    EU_ADEQUACY_COUNTRIES,
    EU_EEA_COUNTRIES,
)


def derive_target_country(target_region: str | None) -> str | None:
    if not target_region:
        return None
    return AWS_REGION_TO_COUNTRY.get(target_region)


def derive_adequacy_decision_exists(target_country: str | None) -> bool:
    if not target_country:
        return False
    return target_country in EU_ADEQUACY_COUNTRIES or target_country in EU_EEA_COUNTRIES


def derive_is_third_country_transfer(
    data_subject_region: str | None,
    target_country: str | None,
) -> bool:
    if data_subject_region not in {"EU", "EEA"}:
        return False

    if not target_country:
        return False

    return target_country not in EU_EEA_COUNTRIES


def build_derived_fields(merged_data: Dict[str, Any]) -> Dict[str, Any]:
    target_region = merged_data.get("target_region")
    data_subject_region = merged_data.get("data_subject_region")

    target_country = derive_target_country(target_region)
    adequacy_decision_exists = derive_adequacy_decision_exists(target_country)
    is_third_country_transfer = derive_is_third_country_transfer(
        data_subject_region=data_subject_region,
        target_country=target_country,
    )

    return {
        "target_country": target_country,
        "adequacy_decision_exists": adequacy_decision_exists,
        "is_third_country_transfer": is_third_country_transfer,
    }