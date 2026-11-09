from fastapi import APIRouter

from backend.llm.providers import CloudflareProvider, GrokProvider, HuggingFaceProvider
from backend.llm.router import RiskLLMRouter
from backend.ml.scorer import ml_scorer
from backend.security.pii import pii_scrubber

router = APIRouter()
llm_router = RiskLLMRouter(providers=[CloudflareProvider(), GrokProvider(), HuggingFaceProvider()])

@router.get("")
def health_check():
    return {"status": "ok", "service": "netvrio-backend"}

@router.get("/providers")
def check_providers():
    def get_status(provider):
        status = provider.health().state.value
        if status == "AVAILABLE":
            return "NOT VERIFIED / CONTRACT TESTED"
        if status in ["UNAVAILABLE", "MISCONFIGURED"]:
            return status
        return "NOT VERIFIED / CONTRACT TESTED"

    res = {}
    names = ["primary", "secondary", "fallback"]
    for i, p in enumerate(llm_router.providers):
        name = names[i] if i < len(names) else f"provider_{i}"
        res[name] = get_status(p)
    return res


@router.get("/components")
def components():
    """Measured status of optional components: PII engine and the ML second-opinion model."""
    return {"pii": pii_scrubber.status(), "ml": ml_scorer.card()}
