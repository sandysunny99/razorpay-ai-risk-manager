import hashlib
import hmac
import json
import os
import time
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, ValidationError

from backend.api.dependencies import get_current_tenant, get_webhook_secret
from backend.api.models import WebhookPayload
from backend.api.ratelimit import ingest_limit, limiter
from backend.audit.audit_log import SqlAuditRepository
from backend.evidence.builder import EvidenceBuilder
from backend.llm.policy import validate_llm_advisory
from backend.llm.providers import CloudflareProvider, GrokProvider, HuggingFaceProvider
from backend.llm.router import RiskLLMRouter
from backend.llm.schemas import RiskLLMRequest
from backend.ml.features import from_live_event
from backend.ml.scorer import escalation_enabled, escalation_threshold, ml_scorer
from backend.observability.tracing import tracer
from backend.policy.engine import PolicyEngine
from backend.policy.models import MerchantPolicy, SecurityValidationResult
from backend.realtime.bus import event_bus
from backend.realtime.velocity import behaviour_tracker
from backend.risk.engine import DeterministicRiskEngine
from backend.risk.models import ActionDecision
from backend.risk.zombie_card_saver import ZombieCardSaver
from backend.runtime_env import demo_mode_enabled
from backend.security.dlp import redact_sensitive_data
from backend.security.hmac import verify_hmac_sha256
from backend.security.idempotency import get_idempotency_store
from backend.security.pii import FREE_TEXT_FIELDS, pii_scrubber
from backend.security.replay import verify_replay
from backend.security.tenant import TenantContext
from backend.threat_intel.exposure import exposure_store
from backend.threat_intel.service import threat_intel
from backend.threat_intel.store import ThreatMatch

router = APIRouter()

risk_engine = DeterministicRiskEngine()
zombie_saver = ZombieCardSaver(allow_raw_reference=False)
evidence_builder = EvidenceBuilder()
llm_router = RiskLLMRouter(providers=[CloudflareProvider(), GrokProvider(), HuggingFaceProvider()])
policy_engine = PolicyEngine()
db_url = os.environ.get("AUDIT_DB_URL", "sqlite:///netvrio_audit.db")
audit_repo = SqlAuditRepository(db_url)



class DemoWebhookData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amount: float
    currency: Optional[str] = "USD"
    ip_address: Optional[str] = None
    user_input: Optional[str] = None
    note: Optional[str] = None
    card_lifecycle: Optional[str] = None
    recent_reuse_count: Optional[int] = None
    trusted_compromise_assertion: Optional[bool] = None
    velocity_1h: Optional[int] = None

class DemoWebhookPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str
    merchant_id: str
    timestamp: int
    event_type: Optional[str] = "payment.attempt"
    token: Optional[str] = None
    data: DemoWebhookData

@router.post("/demo/sign")
async def sign_demo_payload(payload: DemoWebhookPayload):
    # Phase 2: Enforce BOTH NETVRIO_ENV != production AND NETVRIO_DEMO_MODE=true
    if not demo_mode_enabled():
        raise HTTPException(status_code=404, detail="Not Found")

    secret = get_webhook_secret().encode("utf-8")
    body = json.dumps(payload.model_dump(), separators=(',', ':')).encode("utf-8")
    signature = hmac.new(secret, body, hashlib.sha256).hexdigest()

    # `signed_body` is the exact byte sequence that was signed. Browser clients must send
    # it verbatim: re-serializing `payload` in JS changes floats (100.0 -> 100) and breaks HMAC.
    return {
        "signature": signature,
        "payload": json.loads(body.decode("utf-8")),
        "signed_body": body.decode("utf-8"),
    }


def normalize_risk_input(payload_obj: WebhookPayload, safe_payload: dict) -> dict:
    data = safe_payload.get("data", {})
    return {
        "event_id": payload_obj.event_id,
        "merchant_id": payload_obj.merchant_id,
        "customer_id": data.get("customer_id", "unknown"),
        "amount": data.get("amount") if data.get("amount") is not None else 0.0,
        "velocity_1h": data.get("velocity_1h") if data.get("velocity_1h") is not None else 1
    }

def normalize_zombie_input(payload_obj: WebhookPayload, safe_payload: dict) -> dict:
    data = safe_payload.get("data", {})
    return {
        "event_id": payload_obj.event_id,
        "merchant_id": payload_obj.merchant_id,
        "recent_reuse_count": data.get("recent_reuse_count") if data.get("recent_reuse_count") is not None else 0,
        "card_lifecycle": data.get("card_lifecycle", "ACTIVE"),
        "trusted_compromise_assertion": data.get("trusted_compromise_assertion", False)
    }

def normalize_evidence_input(payload_obj: WebhookPayload, safe_payload: dict) -> dict:
    data = safe_payload.get("data", {})
    return {
        "event_id": payload_obj.event_id,
        "merchant_id": payload_obj.merchant_id,
        "timestamp": payload_obj.timestamp,
        "amount": data.get("amount") if data.get("amount") is not None else 0.0,
        "currency": data.get("currency", "USD"),
        "ip_address": data.get("ip_address"),
        "note": data.get("note")
    }

def run_pipeline(
    raw_body: bytes,
    x_signature: Optional[str],
    tenant_id: str,
    webhook_secret: str,
    correlation_id: str,
) -> dict:
    """The single protected decision path. Raises HTTPException on any ingress-security failure.

    Used by the HTTP webhook route, the live traffic generator and the Razorpay adapter so every
    event — synthetic or real — goes through identical controls.
    """
    with tracer.start_as_current_span("process_payment_webhook", record_exception=False) as span:
        span.set_attribute("tenant_id", tenant_id)
        span.set_attribute("correlation_id", correlation_id)

        # 1. HMAC Verification FIRST
        if not x_signature or not verify_hmac_sha256(webhook_secret, raw_body, x_signature):
            span.set_attribute("status", "error_hmac")
            raise HTTPException(status_code=401, detail="Invalid signature")

        # 2. Strict Pydantic Validation
        try:
            payload_obj = WebhookPayload.model_validate_json(raw_body)
            payload = payload_obj.model_dump(exclude_none=True)
            if payload_obj.merchant_id != tenant_id:
                span.set_attribute("status", "error_tenant_mismatch")
                raise HTTPException(status_code=403, detail="Tenant mismatch")
        except ValidationError:
            span.set_attribute("status", "error_validation")
            # `from None` drops the pydantic chain: its message embeds the raw rejected values.
            raise HTTPException(status_code=400, detail="Schema validation failed") from None

        # 2b. Raw PAN is rejected before any state is mutated (idempotency, risk, audit)
        if payload_obj.card_pan or payload_obj.pan:
            span.set_attribute("status", "error_raw_pan")
            raise HTTPException(
                status_code=400,
                detail="Raw account numbers (PAN) are strictly forbidden in this endpoint. "
                "Provide a vaulted token or approved fingerprint.",
            )

        event_id = payload_obj.event_id
        timestamp = payload_obj.timestamp
        merchant_id = payload_obj.merchant_id

        span.set_attribute("event_id", event_id)
        span.set_attribute("merchant_id", merchant_id)

        # 3. Timestamp Verification
        if not verify_replay(event_id, timestamp, tenant_id):
            span.set_attribute("status", "error_replay")
            raise HTTPException(status_code=401, detail="Replay or stale timestamp detected")

        # 4. Tenant Context Isolation Enforced Logically
        with TenantContext(tenant_id):
            # 5. Idempotency Registration
            store = get_idempotency_store()
            if not store.register_event(event_id, tenant_id):
                span.set_attribute("status", "error_idempotency")
                raise HTTPException(status_code=409, detail="Duplicate event")

            # 6. DLP / Redaction
            safe_payload = redact_sensitive_data(payload)
            # 6a. Presidio PII masking of customer free text before evidence, audit, stream or LLM
            pii_found: set = set()
            safe_data = safe_payload.get("data") if isinstance(safe_payload.get("data"), dict) else {}
            for field in FREE_TEXT_FIELDS:
                if isinstance(safe_data.get(field), str):
                    safe_data[field], found = pii_scrubber.scrub(safe_data[field])
                    pii_found.update(found)
            # Telemetry is sanitized implicitly via span processors in production, but we explicitly sanitize span attributes here too

            # Phase 4: Explicit adapters, no arbitrary flattening
            risk_input = normalize_risk_input(payload_obj, safe_payload)
            zombie_input = normalize_zombie_input(payload_obj, safe_payload)

            # 6b. Observed behaviour (sliding windows over accepted traffic) — never lower than supplied signals
            observed = behaviour_tracker.observe(
                tenant_id, risk_input.get("customer_id"), payload_obj.token or payload_obj.fingerprint,
                zombie_input.get("card_lifecycle"),
            )
            if observed["velocity_1h"] is not None:
                risk_input["velocity_1h"] = max(risk_input["velocity_1h"], observed["velocity_1h"])
            if observed["recent_reuse_count"] is not None:
                zombie_input["recent_reuse_count"] = max(zombie_input["recent_reuse_count"], observed["recent_reuse_count"])

            # 6c. Threat intelligence (local indicator store; evidence only, policy still decides)
            raw_data = payload_obj.data if isinstance(payload_obj.data, dict) else {}
            credential_ref = payload_obj.token or payload_obj.fingerprint
            ti_matches = threat_intel.assess(tenant_id, payload_obj.event_id, raw_data.get("ip_address"), credential_ref)
            risk_input["threat_matches"] = [(m.category, m.confidence) for m in ti_matches if m.indicator_type == "ip"]
            if any(m.category == "revoked_token" for m in ti_matches):
                zombie_input["token_revoked"] = True

            # 6d. Card exposure monitoring (fingerprints reported by the exposure collector)
            exposure = exposure_store.is_exposed(tenant_id, payload_obj.token, payload_obj.fingerprint)
            if exposure:
                zombie_input["trusted_compromise_assertion"] = True
                ti_matches.append(ThreatMatch("card", exposure.fingerprint[:7] + "…", exposure.source,
                                              "card_exposed", exposure.confidence))
            exposure_store.link(tenant_id, payload_obj.token, payload_obj.fingerprint)
            evidence_input = normalize_evidence_input(payload_obj, safe_payload)

            # 7. Deterministic Risk
            with tracer.start_as_current_span("deterministic_risk", record_exception=False):
                risk_assessment = risk_engine.analyze(risk_input, correlation_id)
                span.set_attribute("risk_score", risk_assessment.risk_score)
                span.set_attribute("risk_level", risk_assessment.risk_level)

            # 8. Zombie Card Saver
            with tracer.start_as_current_span("zombie_card_saver", record_exception=False):
                zombie_ref = payload_obj.token or payload_obj.fingerprint or "unknown"
                zombie_assessment = zombie_saver.analyze(zombie_ref, tenant_id, merchant_id, zombie_input)

            # 8b. ML second opinion (LightGBM + TreeSHAP reasons). Fail-safe: None when unavailable.
            with tracer.start_as_current_span("ml_second_opinion", record_exception=False):
                exposure_conf = next((m.confidence for m in ti_matches if m.category == "card_exposed"), None)
                ml_assessment = ml_scorer.score(from_live_event(
                    amount=risk_input.get("amount"),
                    velocity=risk_input.get("velocity_1h"),
                    data=raw_data,
                    exposure_confidence=exposure_conf,
                    token_revoked=bool(zombie_input.get("token_revoked")),
                    zombie_signals=list(zombie_assessment.signals),
                    lifecycle=zombie_input.get("card_lifecycle"),
                ))
                ml_escalate = bool(
                    ml_assessment and escalation_enabled() and ml_assessment["probability"] >= escalation_threshold()
                )
                if ml_assessment:
                    ml_assessment["escalation_threshold"] = escalation_threshold()
                    ml_assessment["escalated"] = False

            # 9. Evidence Creation
            with tracer.start_as_current_span("evidence_builder", record_exception=False):
                evidence = evidence_builder.build(evidence_input, risk_assessment.risk_factors, zombie_assessment)

            # 10. LLM Advisory
            with tracer.start_as_current_span("llm_advisory", record_exception=False) as llm_span:
                # Compile trusted evidence IDs for validation
                trusted_evidence_ids = {event_id}
                if evidence and hasattr(evidence, 'evidence_id'):
                    trusted_evidence_ids.add(evidence.evidence_id)
                elif evidence and isinstance(evidence, dict) and "evidence_id" in evidence:
                    trusted_evidence_ids.add(evidence["evidence_id"])
                if risk_assessment and risk_assessment.evidence_ids:
                    trusted_evidence_ids.update(risk_assessment.evidence_ids)
                if zombie_assessment and zombie_assessment.evidence_ids:
                    trusted_evidence_ids.update(zombie_assessment.evidence_ids)

                llm_response = None
                audit_metadata = {}
                try:
                    llm_req = RiskLLMRequest.from_risk_context(
                        event_id=event_id,
                        merchant_id=merchant_id,
                        risk_assessment=risk_assessment,
                        evidence_package=evidence,
                        dlp_payload=payload
                    )
                    llm_response, audit_metadata = llm_router.analyze(llm_req)

                    llm_span.set_attribute("provider", audit_metadata.get("provider", "UNAVAILABLE"))
                    llm_span.set_attribute("llm_status", audit_metadata.get("status", "FAILED"))
                    llm_span.set_attribute("failure_reason", audit_metadata.get("failure_reason", ""))
                    llm_span.set_attribute("latency", audit_metadata.get("latency", 0.0))

                    # Validate evidence citing and prompt injections
                    if llm_response:
                        llm_response = validate_llm_advisory(llm_response, list(trusted_evidence_ids))
                        if not llm_response:
                            llm_span.set_attribute("evidence_validation_failure", True)

                except Exception as e:
                    llm_span.set_attribute("provider_state", "UNAVAILABLE")
                    llm_span.set_attribute("failure_reason", f"EXCEPTION: {type(e).__name__}")
                    llm_response = None

                if llm_response:
                    llm_span.set_attribute("llm_decision", llm_response.recommended_action)
                else:
                    llm_span.set_attribute("llm_decision", "UNAVAILABLE")


            # 11. Deterministic Policy Engine
            with tracer.start_as_current_span("policy_engine", record_exception=False):
                sec_valid = SecurityValidationResult(is_valid_signature=True, is_idempotent=True, is_not_replayed=True, is_valid_tenant=True)
                merchant_policy = MerchantPolicy(merchant_id=merchant_id, auto_block_threshold=90.0, auto_review_threshold=50.0, require_step_up_for_zombie=True)

                zombie_rem = None
                if zombie_assessment.recommendation == "REVOKE_TOKEN":
                    zombie_rem = ActionDecision.BLOCK
                elif zombie_assessment.recommendation == "REQUIRE_STEP_UP":
                    zombie_rem = ActionDecision.REVIEW

                policy_decision = policy_engine.evaluate(
                    risk_assessment=risk_assessment,
                    merchant_policy=merchant_policy,
                    security_validation=sec_valid,
                    zombie_remediation=zombie_rem,
                    ml_escalation=ml_escalate,
                )
                if ml_assessment:
                    ml_assessment["escalated"] = "ML_SECOND_OPINION_REVIEW" in policy_decision.reason_codes
                span.set_attribute("decision", policy_decision.decision)

            # 11b. Feed confirmed outcomes back into threat intelligence
            threat_intel.learn(
                tenant_id,
                token=credential_ref,
                ip_address=raw_data.get("ip_address"),
                zombie_recommendation=getattr(zombie_assessment.recommendation, "value", zombie_assessment.recommendation),
                compromised_source="COMPROMISED_SOURCE" in zombie_assessment.signals,
            )

            # 12. Persistent Audit
            with tracer.start_as_current_span("audit_log", record_exception=False):
                audit_record = {
                    "audit_id": f"aud_{tenant_id}_{event_id}",
                    "event_id": event_id,
                    "merchant_id": merchant_id,
                    "correlation_id": correlation_id,
                    "timestamp": int(time.time()),
                    "record_type": "decision",
                    "decision": policy_decision.decision,
                    "reason_codes": policy_decision.reason_codes,
                    "risk_score": risk_assessment.risk_score,
                    "risk_level": risk_assessment.risk_level,
                    "zombie_detected": len(getattr(zombie_assessment, "signals", [])) > 0,
                    "threat_matches": [{"source": m.source, "category": m.category} for m in ti_matches],
                    "ml_probability": ml_assessment["probability"] if ml_assessment else None,
                }
                audit_hash = audit_repo.append_record(audit_record)

            # 13. Response
            span.set_attribute("status", "success")
            return {
                "correlation_id": correlation_id,
                "event_id": event_id,
                "decision": policy_decision.decision,
                "risk_assessment": risk_assessment.model_dump(),
                "evidence_ids": risk_assessment.evidence_ids,
                "audit_id": audit_record["audit_id"],
                "audit_hash": audit_hash,
                "threat_intel": [m.to_dict() for m in ti_matches],
                "ml_assessment": ml_assessment,
                "pii_masked": sorted(pii_found),
                "zombie_signal": {
                    "impact": getattr(zombie_assessment, 'impact', None),
                    "severity": getattr(zombie_assessment, 'severity', None),
                    "recommendation": getattr(zombie_assessment, 'recommendation', None)
                } if len(getattr(zombie_assessment, 'signals', [])) > 0 else None,
                "ai_advisory": {
                    "provider": audit_metadata.get("provider", "UNAVAILABLE") if audit_metadata else "UNAVAILABLE",
                    "recommended_action": getattr(llm_response, 'recommended_action', 'UNAVAILABLE') if llm_response else 'UNAVAILABLE',
                    "evidence_ids": getattr(llm_response, 'cited_evidence_ids', []) if llm_response else []
                }
            }


def _event_summary(result: dict, payload_meta: dict) -> dict:
    risk = result.get("risk_assessment") or {}
    return {
        "outcome": "DECIDED",
        "event_id": result.get("event_id"),
        "correlation_id": result.get("correlation_id"),
        "decision": result.get("decision"),
        "risk_score": risk.get("risk_score"),
        "risk_level": risk.get("risk_level"),
        "risk_factors": [f.get("name") for f in risk.get("risk_factors", [])],
        "zombie": result.get("zombie_signal"),
        "ai_provider": (result.get("ai_advisory") or {}).get("provider", "UNAVAILABLE"),
        "threat": result.get("threat_intel") or [],
        "ml": result.get("ml_assessment"),
        "pii_masked": result.get("pii_masked") or [],
        "audit_id": result.get("audit_id"),
        **payload_meta,
    }


def _rejection_summary(exc: HTTPException, payload_meta: dict, correlation_id: str) -> dict:
    return {
        "outcome": "REJECTED",
        "event_id": payload_meta.get("event_id"),
        "correlation_id": correlation_id,
        "http_status": exc.status_code,
        "rejected_stage": stage_for_rejection(exc),
        "reason": exc.detail if isinstance(exc.detail, str) else "Rejected",
        **payload_meta,
    }


def stage_for_rejection(exc: HTTPException) -> str:
    """Map the pipeline's own rejection to the control that fired (mirrors the order in run_pipeline)."""
    detail = str(exc.detail).lower()
    if "signature" in detail:
        return "hmac"
    if "tenant" in detail:
        return "tenant"
    if "pan" in detail or "account number" in detail:
        return "pan"
    if "replay" in detail or "stale" in detail:
        return "replay"
    if "duplicate" in detail:
        return "idempotency"
    if exc.status_code in (400, 422):
        return "schema"
    return "unknown"


def _safe_payload_meta(raw_body: bytes) -> dict:
    """Display-only metadata for the live feed. Never includes PAN, tokens or free text."""
    try:
        data = json.loads(raw_body)
    except (ValueError, TypeError):
        return {}
    if not isinstance(data, dict):
        return {}
    inner = data.get("data") if isinstance(data.get("data"), dict) else {}
    amount = inner.get("amount")
    return {
        "event_id": str(data.get("event_id", ""))[:100] or None,
        "amount": amount if isinstance(amount, (int, float)) else None,
        "currency": str(inner.get("currency", ""))[:3] or None,
        "event_type": str(data.get("event_type", ""))[:50] or None,
    }


def process_and_publish(
    raw_body: bytes,
    x_signature: Optional[str],
    tenant_id: str,
    webhook_secret: str,
    correlation_id: str,
    source: str,
    scenario: Optional[str] = None,
) -> dict:
    """run_pipeline + publish the outcome (decision or rejection) to the real-time event bus."""
    started = time.perf_counter()
    meta = {**_safe_payload_meta(raw_body), "source": source}
    if scenario:
        meta["scenario"] = scenario
    try:
        result = run_pipeline(raw_body, x_signature, tenant_id, webhook_secret, correlation_id)
    except HTTPException as exc:
        event = _rejection_summary(exc, meta, correlation_id)
        event["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
        event_bus.publish(tenant_id, event)
        raise
    event = _event_summary(result, meta)
    event["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
    event_bus.publish(tenant_id, event)
    return result


@router.post("/payment")
@limiter.limit(ingest_limit)
async def process_payment_webhook(
    request: Request,
    tenant_id: str = Depends(get_current_tenant),
    webhook_secret: str = Depends(get_webhook_secret),
):
    correlation_id = getattr(request.state, "correlation_id", f"corr_{uuid.uuid4()}")
    raw_body = await request.body()
    result = process_and_publish(
        raw_body, request.headers.get("x-signature"), tenant_id, webhook_secret, correlation_id, source="api"
    )
    return JSONResponse(result)
