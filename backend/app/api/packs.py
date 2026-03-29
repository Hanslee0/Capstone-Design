from fastapi import APIRouter, HTTPException

from app.schemas.pack import (
    PackDetailResponse,
    PackSummaryResponse,
    RuleDetailResponse,
)
from app.services.pack_loader import (
    get_all_rules,
    get_pack_detail,
    get_pack_summary,
    get_rule_by_id,
    load_gdpr_pack,
)

router = APIRouter(prefix="/api/v1/packs", tags=["packs"])


@router.get("/gdpr", response_model=PackSummaryResponse)
def get_gdpr_pack_summary():
    try:
        pack_data = load_gdpr_pack()
        return get_pack_summary(pack_data)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/gdpr/detail", response_model=PackDetailResponse)
def get_gdpr_pack_detail():
    try:
        pack_data = load_gdpr_pack()
        return get_pack_detail(pack_data)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/gdpr/rules", response_model=list[RuleDetailResponse])
def get_gdpr_rules():
    try:
        pack_data = load_gdpr_pack()
        return get_all_rules(pack_data)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/gdpr/rules/{rule_id}", response_model=RuleDetailResponse)
def get_gdpr_rule_by_id(rule_id: str):
    try:
        pack_data = load_gdpr_pack()
        rule = get_rule_by_id(pack_data, rule_id)

        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")

        return rule
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e