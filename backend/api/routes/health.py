import threading
import time

from fastapi import APIRouter, Depends

from backend.api.routes.live import require_demo_mode
from backend.llm.chain import budget, build_all, chain_names, is_configured, scope_all
from backend.llm.schemas import RiskLLMRequest
from backend.ml.scorer import ml_scorer
from backend.security.pii import pii_scrubber

router = APIRouter()

# Last live verification per provider (set by POST /health/providers/verify).
_verified: dict = {}
_verified_lock = threading.Lock()


@router.get("")
def health_check():
    return {"status": "ok", "service": "netvrio-backend"}


def _provider_rows() -> list:
    rows = []
    for p in build_all():
        configured = is_configured(p)
        with _verified_lock:
            last = _verified.get(p.provider_name)
        rows.append({
            "name": p.provider_name,
            "configured": configured,
            "model": getattr(p, "model", None),
            "status": (last or {}).get("status") or ("NOT VERIFIED" if configured else "NOT CONFIGURED"),
            "latency_ms": (last or {}).get("latency_ms"),
            "detail": (last or {}).get("detail"),
            "checked_at": (last or {}).get("checked_at"),
        })
    return rows


@router.get("/providers")
def check_providers():
    """AI advisory chain in fallback order. Keys are never returned, only whether one is set."""
    rows = _provider_rows()
    legacy = {}
    for label, row in zip(("primary", "secondary", "fallback"), rows):
        legacy[label] = row["status"] if row["configured"] else "MISCONFIGURED"
    return {
        **legacy,
        "chain": rows,
        "order": chain_names(),
        "scope": "all" if scope_all() else "flagged",
        "budget": budget.used(),
    }


@router.post("/providers/verify")
def verify_providers(_: None = Depends(require_demo_mode)):
    """Send one synthetic, masked request to each configured provider and record the outcome."""
    req = RiskLLMRequest(
        event_id="evt_health_check", merchant_id="health", amount=1000.0, currency="INR", risk_level="MEDIUM",
        risk_score=50, evidence_summary=[], evidence_package_id="ev_health_check", transaction_context={},
        request_type="payment",
    )
    for p in build_all():
        if not is_configured(p):
            continue
        started = time.perf_counter()
        resp = p.analyze(req, timeout=15.0)
        result = {
            "status": "AVAILABLE" if resp.status == "SUCCESS" else resp.status,
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "detail": None if resp.status == "SUCCESS" else (resp.explanation or "")[:160],
            "checked_at": int(time.time()),
        }
        with _verified_lock:
            _verified[p.provider_name] = result
    return check_providers()


@router.get("/components")
def components():
    """Measured status of optional components: PII engine and the ML second-opinion model."""
    return {"pii": pii_scrubber.status(), "ml": ml_scorer.card()}
