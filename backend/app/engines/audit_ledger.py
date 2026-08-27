from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.entities import AuditEvent


class AuditLedgerEngine:
    """
    Tamper-Evident Hash-Chained Audit Log Engine.
    Guarantees cryptographic verification of all agent decisions and gateway remediations.

    Each block (AuditEvent) contains:
    current_hash = SHA256(event_id + actor + decision + risk_score + policy + action + verification + details + previous_hash)
    """

    GENESIS_HASH = "0" * 64

    @classmethod
    def calculate_event_hash(
        cls,
        event_id: str,
        actor: str,
        decision: str,
        risk_score: float,
        policy: str,
        tool: Optional[str],
        action_requested: Optional[str],
        action_executed: Optional[str],
        verification: Optional[str],
        details: Dict[str, Any],
        previous_hash: str
    ) -> str:
        payload = {
            "event_id": event_id,
            "actor": actor,
            "decision": decision,
            "risk_score": float(risk_score),
            "policy": policy,
            "tool": tool or "",
            "action_requested": action_requested or "",
            "action_executed": action_executed or "",
            "verification": verification or "",
            "details": details,
            "previous_hash": previous_hash
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def append_event(
        cls,
        db: Session,
        event_id: str,
        actor: str,
        decision: str,
        risk_score: float,
        policy: str,
        tool: Optional[str],
        action_requested: Optional[str],
        action_executed: Optional[str],
        verification: Optional[str],
        details: Dict[str, Any]
    ) -> AuditEvent:
        # Fetch the latest event to obtain previous_hash
        latest_event = db.query(AuditEvent).order_by(AuditEvent.id.desc()).first()
        prev_hash = latest_event.current_hash if latest_event and latest_event.current_hash else cls.GENESIS_HASH

        curr_hash = cls.calculate_event_hash(
            event_id=event_id,
            actor=actor,
            decision=decision,
            risk_score=risk_score,
            policy=policy,
            tool=tool,
            action_requested=action_requested,
            action_executed=action_executed,
            verification=verification,
            details=details,
            previous_hash=prev_hash
        )

        event = AuditEvent(
            event_id=event_id,
            actor=actor,
            agent_decision=decision,
            risk_score=risk_score,
            policy_evaluated=policy,
            tool_used=tool,
            action_requested=action_requested,
            action_executed=action_executed,
            verification_result=verification,
            previous_hash=prev_hash,
            current_hash=curr_hash,
            details=details,
            created_at=datetime.now(timezone.utc)
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @classmethod
    def verify_chain_integrity(cls, db: Session) -> Dict[str, Any]:
        """
        Cryptographically validates the entire audit chain from genesis to head.
        Detects deleted records, modified content, and reordered entries.
        """
        events = db.query(AuditEvent).order_by(AuditEvent.id.asc()).all()
        if not events:
            return {
                "valid": True,
                "total_events": 0,
                "status": "EMPTY_CHAIN",
                "tampered_events": []
            }

        tampered = []
        expected_prev_hash = cls.GENESIS_HASH

        for idx, event in enumerate(events):
            # 1. Check previous_hash link
            if event.previous_hash != expected_prev_hash:
                tampered.append({
                    "event_id": event.event_id,
                    "index": idx,
                    "error": "BROKEN_PREVIOUS_HASH_LINK",
                    "expected_previous_hash": expected_prev_hash,
                    "actual_previous_hash": event.previous_hash
                })

            # 2. Recompute current_hash from record content
            recalculated_hash = cls.calculate_event_hash(
                event_id=event.event_id,
                actor=event.actor,
                decision=event.agent_decision,
                risk_score=event.risk_score,
                policy=event.policy_evaluated,
                tool=event.tool_used,
                action_requested=event.action_requested,
                action_executed=event.action_executed,
                verification=event.verification_result,
                details=event.details or {},
                previous_hash=event.previous_hash
            )

            if event.current_hash != recalculated_hash:
                tampered.append({
                    "event_id": event.event_id,
                    "index": idx,
                    "error": "DATA_INTEGRITY_MISMATCH",
                    "stored_hash": event.current_hash,
                    "recalculated_hash": recalculated_hash
                })

            expected_prev_hash = event.current_hash

        is_valid = (len(tampered) == 0)
        return {
            "valid": is_valid,
            "total_events": len(events),
            "status": "VERIFIED_TAMPER_FREE" if is_valid else "TAMPERING_DETECTED",
            "tampered_events": tampered,
            "head_hash": events[-1].current_hash if events else None
        }
