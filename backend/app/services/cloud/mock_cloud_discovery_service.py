from typing import Any, Dict


def _default_aws_region(destination_country: str) -> str:
    country = destination_country.strip().lower()

    if country in ["brazil", "brasil", "브라질"]:
        return "sa-east-1"

    if country in ["korea", "south korea", "대한민국", "한국"]:
        return "ap-northeast-2"

    if country in ["germany", "france", "eu", "european union", "독일", "유럽연합"]:
        return "eu-central-1"

    if country in ["saudi arabia", "saudi", "사우디", "사우디아라비아"]:
        return "me-south-1"

    return "us-east-1"


def _default_azure_location(destination_country: str) -> str:
    country = destination_country.strip().lower()

    if country in ["brazil", "brasil", "브라질"]:
        return "brazilsouth"

    if country in ["korea", "south korea", "대한민국", "한국"]:
        return "koreacentral"

    if country in ["germany", "france", "eu", "european union", "독일", "유럽연합"]:
        return "germanywestcentral"

    return "eastus"


def discover_mock_cloud(
    cloud_provider: str,
    destination_country: str,
    resource: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    resource = resource or {}
    provider = cloud_provider.strip().lower()

    if provider == "aws":
        region = resource.get("region") or _default_aws_region(destination_country)

        return {
            "cloud_provider": "aws",
            "resource_type": resource.get("resource_type", "s3"),
            "current_region": resource.get("current_region", "ap-northeast-2"),
            "region": region,
            "data_type": resource.get("data_type", "personal_data"),
            "contains_sensitive_data": resource.get("contains_sensitive_data", True),
            "encryption_at_rest": resource.get("encryption_at_rest", True),
            "encryption_in_transit": resource.get("encryption_in_transit", True),
            "access_control_in_place": resource.get("access_control_in_place", True),
        }

    if provider == "azure":
        location = resource.get("location") or _default_azure_location(destination_country)

        return {
            "cloud_provider": "azure",
            "resource_type": resource.get("resource_type", "storage_account"),
            "current_region": resource.get("current_region", "koreacentral"),
            "location": location,
            "data_type": resource.get("data_type", "personal_data"),
            "contains_sensitive_data": resource.get("contains_sensitive_data", True),
            "encryption_at_rest": resource.get("encryption_at_rest", True),
            "encryption_in_transit": resource.get("encryption_in_transit", True),
            "access_control_in_place": resource.get("access_control_in_place", True),
        }

    return {
        "cloud_provider": "manual",
        "data_type": resource.get("data_type", "personal_data"),
    }