from fastapi import APIRouter, Depends

from backend.api.dependencies import get_current_tenant

router = APIRouter()

@router.post("/analyze")
def manual_analyze(tenant_id: str = Depends(get_current_tenant)):
    # Stub for manual risk analysis endpoint
    return {"status": "STUB"}
