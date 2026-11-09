from fastapi import APIRouter, Depends, HTTPException

from backend.api.dependencies import get_current_tenant

router = APIRouter()

# Stub Case Repository for prototype
_in_memory_cases = {}

@router.get("/{case_id}")
def get_case(case_id: str, tenant_id: str = Depends(get_current_tenant)):
    case = _in_memory_cases.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Enforce tenant isolation at repository level
    if case.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=404, detail="Case not found") # 404 instead of 403 to prevent enumeration

    return case
