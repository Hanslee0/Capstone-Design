from typing import Any, Dict, List, Optional

from app.services.file_loader import load_json_file
from app.utils.path_helper import get_policy_pack_path


def load_gdpr_pack(file_name: str = "gdpr_pack_v2.json") -> Dict[str, Any]:
    pack_path = get_policy_pack_path() / file_name
    pack_data = load_json_file(pack_path)
    validate_pack_structure(pack_data)
    return pack_data


def validate_pack_structure(pack_data: Dict[str, Any]) -> None:
    required_top_keys = [
        "pack_id",
        "pack_name",
        "jurisdiction",
        "version",
        "description",
        "source",
        "decision_priority",
        "scoring_policy",
        "rules",
    ]

    missing_keys = [key for key in required_top_keys if key not in pack_data]
    if missing_keys:
        raise ValueError(f"Missing required pack keys: {', '.join(missing_keys)}")

    if not isinstance(pack_data["rules"], list):
        raise ValueError("'rules' must be a list")

    for idx, rule in enumerate(pack_data["rules"]):
        validate_rule_structure(rule, idx)


def validate_rule_structure(rule: Dict[str, Any], idx: int) -> None:
    required_rule_keys = [
        "rule_id",
        "article",
        "title",
        "category",
        "priority",
        "decision",
        "risk_score_delta",
        "compliance_score_delta",
        "when",
        "required_evidence",
        "required_actions",
        "message",
        "references",
    ]

    missing_keys = [key for key in required_rule_keys if key not in rule]
    if missing_keys:
        raise ValueError(
            f"Rule at index {idx} is missing keys: {', '.join(missing_keys)}"
        )


def get_pack_summary(pack_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "pack_id": pack_data["pack_id"],
        "pack_name": pack_data["pack_name"],
        "jurisdiction": pack_data["jurisdiction"],
        "version": pack_data["version"],
        "description": pack_data["description"],
        "included_articles": pack_data["source"].get("included_articles", []),
        "rule_count": len(pack_data["rules"]),
    }


def get_pack_detail(pack_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "pack_id": pack_data["pack_id"],
        "pack_name": pack_data["pack_name"],
        "jurisdiction": pack_data["jurisdiction"],
        "version": pack_data["version"],
        "description": pack_data["description"],
        "source": pack_data["source"],
        "decision_priority": pack_data["decision_priority"],
        "scoring_policy": pack_data["scoring_policy"],
        "rule_count": len(pack_data["rules"]),
        "qualitative_review_templates": pack_data.get(
            "qualitative_review_templates", {}
        ),
    }


def get_all_rules(pack_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return pack_data["rules"]


def get_rule_by_id(pack_data: Dict[str, Any], rule_id: str) -> Optional[Dict[str, Any]]:
    for rule in pack_data["rules"]:
        if rule["rule_id"] == rule_id:
            return rule
    return None