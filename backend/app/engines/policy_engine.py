from typing import Dict, Any, Optional
from app.core.config import settings

class PolicyEngine:
    """
    Mandatory Policy & Guardrail Engine.
    Strictly gates agent actions before execution:
    - AUTO_EXECUTE: Action allowed immediately (e.g. Token Revocation on critical risk / zombie tokens).
    - REVIEW_REQUIRED: Action blocked pending human supervisor approval (e.g. Card Suspension).
    - NEVER_EXECUTE: Action forbidden by policy (e.g. unverified financial transfers).
    - DENIED: Risk threshold not met for the requested remediation.
    """

    def __init__(self, merchant_policy: Optional[Dict[str, Any]] = None):
        self.merchant_policy = merchant_policy or {}

    POLICY_VERSION = "v2026.08.1"

    def evaluate_action(self, action_name: str, risk_score: float, context: Dict[str, Any]) -> Dict[str, Any]:
        auto_revoke_allowed = self.merchant_policy.get(
            "auto_revoke_token", settings.AUTO_REVOKE_TOKEN_ON_CRITICAL
        )
        auto_suspend_allowed = self.merchant_policy.get(
            "auto_suspend_card", settings.AUTO_SUSPEND_CARD_ON_CRITICAL
        )
        critical_thresh = self.merchant_policy.get(
            "critical_threshold", settings.THRESHOLD_CRITICAL
        )

        is_zombie = context.get("is_zombie", False)

        # 1. Token Revocation Policy
        if action_name in ["revoke_token", "TOKEN_REVOCATION"]:
            if is_zombie or risk_score >= critical_thresh:
                if auto_revoke_allowed:
                    return {
                        "action": action_name,
                        "decision": "AUTO_EXECUTE",
                        "allowed": True,
                        "requires_approval": False,
                        "approval_required": False,
                        "risk_score": risk_score,
                        "policy_version": self.POLICY_VERSION,
                        "authorization_scope": "PAYMENT_TOKEN_REMEDIATION",
                        "reason": f"Policy Rule PR-01: Auto-revocation permitted (Risk {risk_score} >= {critical_thresh} or Zombie Token = {is_zombie})"
                    }
                else:
                    return {
                        "action": action_name,
                        "decision": "REVIEW_REQUIRED",
                        "allowed": False,
                        "requires_approval": True,
                        "approval_required": True,
                        "risk_score": risk_score,
                        "policy_version": self.POLICY_VERSION,
                        "authorization_scope": "PAYMENT_TOKEN_REMEDIATION",
                        "reason": "Merchant policy disabled auto-revocation; human review required"
                    }
            elif risk_score >= 60.0:
                return {
                    "action": action_name,
                    "decision": "REVIEW_REQUIRED",
                    "allowed": False,
                    "requires_approval": True,
                    "approval_required": True,
                    "risk_score": risk_score,
                    "policy_version": self.POLICY_VERSION,
                    "authorization_scope": "PAYMENT_TOKEN_REMEDIATION",
                    "reason": f"High risk ({risk_score}), but below critical threshold ({critical_thresh}). SOC analyst sign-off required."
                }
            else:
                return {
                    "action": action_name,
                    "decision": "DENIED",
                    "allowed": False,
                    "requires_approval": False,
                    "approval_required": False,
                    "risk_score": risk_score,
                    "policy_version": self.POLICY_VERSION,
                    "authorization_scope": "PAYMENT_TOKEN_REMEDIATION",
                    "reason": f"Policy Rule PR-03: Action denied. Risk score {risk_score} is below remediation threshold (60.0)"
                }

        # 2. Card Suspension Policy
        if action_name in ["suspend_card", "CARD_SUSPENSION"]:
            if auto_suspend_allowed and risk_score >= 95.0:
                return {
                    "action": action_name,
                    "decision": "AUTO_EXECUTE",
                    "allowed": True,
                    "requires_approval": False,
                    "approval_required": False,
                    "risk_score": risk_score,
                    "policy_version": self.POLICY_VERSION,
                    "authorization_scope": "CARD_LIFECYCLE_CONTROL",
                    "reason": "Policy Rule PR-04: Card auto-suspension enabled by merchant override"
                }
            else:
                return {
                    "action": action_name,
                    "decision": "REVIEW_REQUIRED",
                    "allowed": False,
                    "requires_approval": True,
                    "approval_required": True,
                    "risk_score": risk_score,
                    "policy_version": self.POLICY_VERSION,
                    "authorization_scope": "CARD_LIFECYCLE_CONTROL",
                    "reason": "Policy Guardrail PG-CARD-01: Card suspension is high-friction customer action. Human supervisor review is strictly MANDATORY."
                }

        # 3. Financial Transfers / Chargebacks
        if action_name in ["transfer_funds", "auto_refund"]:
            return {
                "action": action_name,
                "decision": "NEVER_EXECUTE",
                "allowed": False,
                "requires_approval": False,
                "approval_required": False,
                "risk_score": risk_score,
                "policy_version": self.POLICY_VERSION,
                "authorization_scope": "FINANCIAL_MOVEMENT_FORBIDDEN",
                "reason": "Policy Guardrail PG-FIN-01: Autonomous financial movement is strictly prohibited by security architecture."
            }

        # 4. Case Creation / Alerting (Always permitted)
        if action_name in ["create_security_case", "alert_soc", "record_audit"]:
            return {
                "action": action_name,
                "decision": "AUTO_EXECUTE",
                "allowed": True,
                "requires_approval": False,
                "approval_required": False,
                "risk_score": risk_score,
                "policy_version": self.POLICY_VERSION,
                "authorization_scope": "INCIDENT_LOGGING",
                "reason": "Observability and security case creation is universally permitted."
            }

        return {
            "action": action_name,
            "decision": "REVIEW_REQUIRED",
            "allowed": False,
            "requires_approval": True,
            "approval_required": True,
            "risk_score": risk_score,
            "policy_version": self.POLICY_VERSION,
            "authorization_scope": "UNKNOWN_SCOPE",
            "reason": f"Unclassified action '{action_name}' requires human approval."
        }
