from typing import Any, Dict, List, Optional


COUNTRY_TO_EXPORT_PACK = {
    # Korea
    "korea": "korea_pipa",
    "south korea": "korea_pipa",
    "republic of korea": "korea_pipa",
    "대한민국": "korea_pipa",
    "한국": "korea_pipa",

    # Brazil
    "brazil": "lgpd",
    "brasil": "lgpd",
    "브라질": "lgpd",

    # EU / GDPR demo mapping
    "eu": "gdpr",
    "eea": "gdpr",
    "european union": "gdpr",
    "germany": "gdpr",
    "france": "gdpr",
    "ireland": "gdpr",
    "netherlands": "gdpr",
    "spain": "gdpr",
    "italy": "gdpr",
    "유럽연합": "gdpr",
    "독일": "gdpr",
    "프랑스": "gdpr",

    # Saudi
    "saudi arabia": "saudi_pdpl",
    "saudi": "saudi_pdpl",
    "사우디": "saudi_pdpl",
    "사우디아라비아": "saudi_pdpl",

    # Taiwan
    "taiwan": "taiwan",
    "대만": "taiwan",
}

COUNTRY_TO_DESTINATION_PACK = {
    "eu": "gdpr_destination",
    "eea": "gdpr_destination",
    "european union": "gdpr_destination",

    "korea": "korea_pipa_destination",
    "south korea": "korea_pipa_destination",
    "republic of korea": "korea_pipa_destination",
    "대한민국": "korea_pipa_destination",
    "한국": "korea_pipa_destination",

    "brazil": "lgpd_destination",
    "brasil": "lgpd_destination",
    "브라질": "lgpd_destination",

    "saudi arabia": "saudi_pdpl_destination",
    "saudi": "saudi_pdpl_destination",
    "사우디": "saudi_pdpl_destination",
    "사우디아라비아": "saudi_pdpl_destination",

    "taiwan": "taiwan_destination",
    "대만": "taiwan_destination",
}

def normalize_country_name(country: str) -> str:
    return country.strip().lower()


def resolve_export_pack_id_by_country(country: str) -> Optional[str]:
    if not country:
        return None

    normalized = normalize_country_name(country)
    return COUNTRY_TO_EXPORT_PACK.get(normalized)


def resolve_destination_pack_id_by_country(country: str) -> Optional[str]:
    if not country:
        return None

    normalized = normalize_country_name(country)
    return COUNTRY_TO_DESTINATION_PACK.get(normalized)


def build_applicable_pack_plan(
    origin_country: str,
    destination_country: str,
    include_destination_reference: bool = True,
    extra_pack_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    2안 구조:
    - 출발국 법령 = primary
    - 도착국 법령 = reference
    - 사용자가 추가 선택한 법령 = reference
    """

    primary_pack_id = resolve_export_pack_id_by_country(origin_country)

    if not primary_pack_id:
        raise ValueError(
            f"Unsupported origin_country: {origin_country}. "
            "Add this country to COUNTRY_TO_PACK first."
        )

    applications: List[Dict[str, str]] = [
        {
            "pack_id": primary_pack_id,
            "country": origin_country,
            "role": "primary_export_law",
            "reason": "출발국가 기준 주 적용 법령입니다.",
        }
    ]

    reference_pack_ids: List[str] = []

    destination_pack_id = resolve_destination_pack_id_by_country(destination_country)
    if (
        include_destination_reference
        and destination_pack_id
        and destination_pack_id != primary_pack_id
    ):
        reference_pack_ids.append(destination_pack_id)
        applications.append(
            {
                "pack_id": destination_pack_id,
                "country": destination_country,
                "role": "destination_compliance",
                "reason": "도착국 내 처리 적법성 검토 정책팩입니다.",
            }
        )

    for pack_id in extra_pack_ids or []:
        if pack_id == primary_pack_id:
            continue
        if pack_id in reference_pack_ids:
            continue

        reference_pack_ids.append(pack_id)
        applications.append(
            {
                "pack_id": pack_id,
                "country": "manual",
                "role": "additional_reference_law",
                "reason": "사용자가 추가 선택한 참고 검토 법령입니다.",
            }
        )

    return {
        "origin_country": origin_country,
        "destination_country": destination_country,
        "primary_pack_id": primary_pack_id,
        "reference_pack_ids": reference_pack_ids,
        "applications": applications,
    }