from typing import Any, Dict, Optional


AWS_REGION_TO_COUNTRY = {
    "ap-northeast-2": "Korea",
    "sa-east-1": "Brazil",
    "eu-central-1": "Germany",
    "eu-west-1": "Ireland",
    "us-east-1": "United States",
    "me-south-1": "Saudi Arabia",
    "ap-northeast-1": "Japan",
}


AZURE_LOCATION_TO_COUNTRY = {
    "koreacentral": "Korea",
    "brazilsouth": "Brazil",
    "germanywestcentral": "Germany",
    "westeurope": "Netherlands",
    "eastus": "United States",
}


def normalize_cloud_input(
    raw_data: Dict[str, Any],
    destination_country: Optional[str] = None,
) -> Dict[str, Any]:
    provider = str(
        raw_data.get("cloud_provider")
        or raw_data.get("provider")
        or "manual"
    ).lower()

    region = (
        raw_data.get("target_region")
        or raw_data.get("region")
        or raw_data.get("location")
    )

    target_country = raw_data.get("target_country")

    if not target_country and provider == "aws":
        target_country = AWS_REGION_TO_COUNTRY.get(region)

    if not target_country and provider == "azure":
        target_country = AZURE_LOCATION_TO_COUNTRY.get(region)

    if not target_country:
        target_country = destination_country

    normalized = {
        "cloud_provider": provider,
        "current_region": raw_data.get("current_region", "unknown"),
        "target_region": region,
        "target_country": target_country,
        "data_type": raw_data.get("data_type", "personal_data"),
        "contains_sensitive_data": raw_data.get("contains_sensitive_data", False),
        "encryption_at_rest": raw_data.get("encryption_at_rest", False),
        "encryption_in_transit": raw_data.get("encryption_in_transit", False),
        "access_control_in_place": raw_data.get("access_control_in_place", False),
    }

    return {key: value for key, value in normalized.items() if value is not None}