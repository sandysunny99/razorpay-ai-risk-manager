import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .errors import SensitiveDataDetected

FORBIDDEN_KEYS = {"card_pan", "pan", "cvv", "pin", "api_key", "secret", "password", "token", "jwt", "authorization"}

class RiskLLMRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    merchant_id: str
    amount: float
    currency: str
    risk_level: str
    risk_score: int
    risk_features: Optional[Dict[str, Any]] = None
    zombie_signal: Optional[Dict[str, Any]] = None
    evidence_package_id: str = ""
    evidence_summary: List[str]
    transaction_context: Optional[Dict[str, Any]] = None
    request_type: str = "payment"
    zombie_severity: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def recursive_check_secrets(cls, data: Any) -> Any:
        def scan_val(v: Any):
            if isinstance(v, dict):
                for k, val in v.items():
                    if isinstance(k, str) and k.lower() in FORBIDDEN_KEYS:
                        raise SensitiveDataDetected(f"Forbidden key '{k}' detected in nested payload")
                    scan_val(val)
            elif isinstance(v, list):
                for item in v:
                    scan_val(item)
            elif isinstance(v, str):
                v_lower = v.lower()
                if "41112222" in v.replace(" ", "") or "secret_" in v_lower:
                    raise SensitiveDataDetected("Potential secret or PAN detected in LLM payload string")
                if re.search(r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}', v):
                    raise SensitiveDataDetected("Potential JWT detected in LLM payload string")

        scan_val(data)
        return data

    @classmethod
    def from_risk_context(cls, event_id: str, merchant_id: str, risk_assessment: Any, evidence_package: Any, dlp_payload: dict):
        for k in FORBIDDEN_KEYS:
            if k in dlp_payload or k in dlp_payload.get("data", {}):
                raise SensitiveDataDetected(f"Forbidden key {k} present in context before LLM call")

        z_severity = None
        z_signal = None
        if hasattr(risk_assessment, "zombie_signal") and risk_assessment.zombie_signal:
            z_signal = risk_assessment.zombie_signal
            z_severity = risk_assessment.zombie_signal.get("severity")

        ev_summary = [e.description for e in evidence_package.items]
        ev_id = getattr(evidence_package, "evidence_id", evidence_package.get("evidence_id") if isinstance(evidence_package, dict) else event_id)

        # Build features dict safely
        risk_features = {}
        if hasattr(risk_assessment, 'risk_factors') and risk_assessment.risk_factors:
            for factor in risk_assessment.risk_factors:
                if isinstance(factor, dict):
                    risk_features[factor.get("reason", "unknown")] = True
                elif hasattr(factor, "reason"):
                    risk_features[factor.reason] = True

        return cls(
            event_id=event_id,
            merchant_id=merchant_id,
            amount=float(dlp_payload.get("data", {}).get("amount", 0.0)),
            currency=dlp_payload.get("data", {}).get("currency", "USD"),
            risk_level=getattr(risk_assessment.risk_level, 'value', risk_assessment.risk_level) if hasattr(risk_assessment, 'risk_level') else "UNKNOWN",
            risk_score=int(risk_assessment.risk_score),
            risk_features=risk_features,
            zombie_signal=z_signal,
            evidence_package_id=ev_id,
            evidence_summary=ev_summary,
            transaction_context={"ip_network": _ip_network(dlp_payload.get("data", {}).get("ip_address"))},
            request_type="payment",
            zombie_severity=z_severity
        )

def _ip_network(value) -> str:
    """Customer IPs are personal data: an external LLM only ever sees the /24 (IPv4) or /48 (IPv6)."""
    import ipaddress

    try:
        ip = ipaddress.ip_address(str(value).strip())
    except ValueError:
        return "unknown"
    prefix = 24 if ip.version == 4 else 48
    return str(ipaddress.ip_network(f"{ip}/{prefix}", strict=False))


class RiskLLMResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., pattern="^(SUCCESS|UNAVAILABLE|ERROR|TIMEOUT|INVALID|MISCONFIGURED)$")
    recommended_action: Optional[str] = Field(None, pattern="^(ALLOW|REVIEW|BLOCK|REQUIRE_STEP_UP|QUARANTINE)$")
    confidence: Optional[int] = Field(None, ge=0, le=100)
    explanation: Optional[str] = None
    cited_evidence_ids: List[str] = []
    provider: Optional[str] = None
    model: Optional[str] = None
    request_id: Optional[str] = None
    latency_ms: Optional[int] = None

    @model_validator(mode='after')
    def validate_success(self):
        if self.status == "SUCCESS" and self.recommended_action is None:
            raise ValueError("recommended_action is required when status is SUCCESS")
        return self
