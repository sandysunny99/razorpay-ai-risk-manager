from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.core.config import settings


@dataclass
class RiskPolicyConfig:
    """
    Centralized, deterministic configuration for risk boundaries and response tiers.
    All boundaries are explicitly defined and justified by validation set empirical sweeps.
    """
    monitor_threshold: float = 35.0
    broad_detection_threshold: float = 40.0
    step_up_threshold: float = 40.0
    review_threshold: float = 65.0
    auto_execute_threshold: float = 75.0
    auto_revoke_token: bool = True
    auto_suspend_card: bool = False
    policy_version: str = "v2026.08.2-tiered"

class PolicyEngine:
    """
    Mandatory Policy & Guardrail Engine.
    Strictly gates agent actions before execution and determines response tiers:
    - ALLOW: Normal legitimate traffic (Risk < 35.0, Level 0 screening).
    - MONITOR: Low anomaly (35.0 <= Risk < 45.0, Level 1 light telemetry).
    - STEP_UP_REQUIRED: Defensible friction (45.0 <= Risk < 65.0, Level 2 Step-Up 2FA Challenge).
    - REVIEW_REQUIRED: Security review (65.0 <= Risk < 75.0 or Card Suspension, Level 2 SOC Case).
    - AUTO_EXECUTE: Autonomous action allowed (Risk >= 75.0 or Zombie Token, Level 3 Token Revocation).
    - NEVER_EXECUTE: Forbidden by architecture (Financial transfers/refunds).
    """

    POLICY_VERSION = "v2026.08.2-tiered"

    def __init__(self, merchant_policy: Optional[Dict[str, Any]] = None, config: Optional[RiskPolicyConfig] = None):
        self.merchant_policy = merchant_policy or {}
        self.config = config or RiskPolicyConfig(
            monitor_threshold=self.merchant_policy.get("monitor_threshold", 35.0),
            broad_detection_threshold=self.merchant_policy.get("broad_detection_threshold", 40.0),
            step_up_threshold=self.merchant_policy.get("step_up_threshold", 40.0),
            review_threshold=self.merchant_policy.get("review_threshold", 65.0),
            auto_execute_threshold=self.merchant_policy.get("auto_execute_threshold", settings.THRESHOLD_CRITICAL),
            auto_revoke_token=self.merchant_policy.get("auto_revoke_token", settings.AUTO_REVOKE_TOKEN_ON_CRITICAL),
            auto_suspend_card=self.merchant_policy.get("auto_suspend_card", settings.AUTO_SUSPEND_CARD_ON_CRITICAL),
        )

    def classify_risk_tier(self, risk_score: float, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Deterministic mapping from continuous risk score to response tier and policy decision.
        Distinguishes Detection Status (Clean vs Suspicious) from Autonomous Response Tier.
        """
        ctx = context or {}
        is_zombie = ctx.get("is_zombie", False) or ctx.get("is_zombie_token", False)

        # 1. Broad Detection Layer (Boundary = 40.0 based on validation set)
        detection_status = "SUSPICIOUS" if risk_score >= self.config.broad_detection_threshold or is_zombie else "CLEAN"

        # 2. Response Tier & Policy Decision
        if is_zombie or risk_score >= self.config.auto_execute_threshold:
            risk_level = "CRITICAL"
            response_tier = "AUTO_REMEDIATE"
            policy_decision = "AUTO_EXECUTE"
            recommended_action = "REVOKE_TOKEN"
            requires_approval = False
            investigation_level = 3
            reason = f"Critical risk ({risk_score:.1f} >= {self.config.auto_execute_threshold}) or Zombie token ({is_zombie}). Autonomous token revocation authorized."
        elif risk_score >= self.config.review_threshold:
            risk_level = "HIGH"
            response_tier = "REVIEW"
            policy_decision = "REVIEW_REQUIRED"
            recommended_action = "SECURITY_REVIEW"
            requires_approval = True
            investigation_level = 2
            reason = f"High risk ({risk_score:.1f} >= {self.config.review_threshold}). Escalated to SOC analyst review."
        elif risk_score >= self.config.step_up_threshold:
            risk_level = "HIGH"
            response_tier = "STEP_UP"
            policy_decision = "STEP_UP_REQUIRED"
            recommended_action = "REQUEST_STEP_UP"
            requires_approval = False
            investigation_level = 2
            reason = f"Sub-critical anomaly ({risk_score:.1f} >= {self.config.step_up_threshold}). Step-up verification challenge initiated."
        elif risk_score >= self.config.monitor_threshold:
            risk_level = "MEDIUM"
            response_tier = "MONITOR"
            policy_decision = "MONITOR"
            recommended_action = "MONITOR"
            requires_approval = False
            investigation_level = 1
            reason = f"Moderate baseline signal ({risk_score:.1f} >= {self.config.monitor_threshold}). Enhanced post-authorization telemetry monitoring."
        else:
            risk_level = "LOW"
            response_tier = "LOW"
            policy_decision = "ALLOW"
            recommended_action = "ALLOW"
            requires_approval = False
            investigation_level = 0
            reason = f"Clean payment profile ({risk_score:.1f} < {self.config.monitor_threshold}). Fast-path authorization allowed."

        return {
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "detection_status": detection_status,
            "response_tier": response_tier,
            "policy_decision": policy_decision,
            "recommended_action": recommended_action,
            "requires_approval": requires_approval,
            "investigation_level": investigation_level,
            "policy_version": self.config.policy_version,
            "reason": reason
        }

    def evaluate_action(self, action_name: str, risk_score: float, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates whether a specific remedial or operational action is permitted under policy guardrails.
        """
        is_zombie = context.get("is_zombie", False) or context.get("is_zombie_token", False)

        # 1. Token Revocation Policy (Autonomous only on Critical / Zombie)
        if action_name in ["revoke_token", "TOKEN_REVOCATION"]:
            if is_zombie or risk_score >= self.config.auto_execute_threshold:
                if self.config.auto_revoke_token:
                    return {
                        "action": action_name,
                        "decision": "AUTO_EXECUTE",
                        "allowed": True,
                        "requires_approval": False,
                        "approval_required": False,
                        "risk_score": risk_score,
                        "policy_version": self.config.policy_version,
                        "authorization_scope": "PAYMENT_TOKEN_REMEDIATION",
                        "reason": f"Policy Rule PR-01: Auto-revocation permitted (Risk {risk_score} >= {self.config.auto_execute_threshold} or Zombie Token = {is_zombie})"
                    }
                else:
                    return {
                        "action": action_name,
                        "decision": "REVIEW_REQUIRED",
                        "allowed": False,
                        "requires_approval": True,
                        "approval_required": True,
                        "risk_score": risk_score,
                        "policy_version": self.config.policy_version,
                        "authorization_scope": "PAYMENT_TOKEN_REMEDIATION",
                        "reason": "Merchant policy disabled auto-revocation; human review required"
                    }
            elif risk_score >= self.config.step_up_threshold:
                return {
                    "action": action_name,
                    "decision": "REVIEW_REQUIRED",
                    "allowed": False,
                    "requires_approval": True,
                    "approval_required": True,
                    "risk_score": risk_score,
                    "policy_version": self.config.policy_version,
                    "authorization_scope": "PAYMENT_TOKEN_REMEDIATION",
                    "reason": f"Sub-critical risk ({risk_score:.1f} < {self.config.auto_execute_threshold}). Token revocation requires SOC sign-off."
                }
            else:
                return {
                    "action": action_name,
                    "decision": "DENIED",
                    "allowed": False,
                    "requires_approval": False,
                    "approval_required": False,
                    "risk_score": risk_score,
                    "policy_version": self.config.policy_version,
                    "authorization_scope": "PAYMENT_TOKEN_REMEDIATION",
                    "reason": f"Policy Rule PR-03: Action denied. Risk score {risk_score:.1f} is below remediation threshold ({self.config.step_up_threshold})"
                }

        # 2. Step-Up Verification Policy (Simulated Challenge)
        if action_name in ["request_step_up", "REQUEST_STEP_UP", "verify_step_up", "VERIFY_STEP_UP"]:
            return {
                "action": action_name,
                "decision": "AUTO_EXECUTE",
                "allowed": True,
                "requires_approval": False,
                "approval_required": False,
                "risk_score": risk_score,
                "policy_version": self.config.policy_version,
                "authorization_scope": "CUSTOMER_DEFENSIVE_CHALLENGE",
                "reason": "Defensive 2FA step-up challenge execution is permitted."
            }

        # 3. Card Suspension Policy (Strictly Human Review Required)
        if action_name in ["suspend_card", "CARD_SUSPENSION"]:
            if self.config.auto_suspend_card and risk_score >= 95.0:
                return {
                    "action": action_name,
                    "decision": "AUTO_EXECUTE",
                    "allowed": True,
                    "requires_approval": False,
                    "approval_required": False,
                    "risk_score": risk_score,
                    "policy_version": self.config.policy_version,
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
                    "policy_version": self.config.policy_version,
                    "authorization_scope": "CARD_LIFECYCLE_CONTROL",
                    "reason": "Policy Guardrail PG-CARD-01: Card suspension is high-friction customer action. Human supervisor review is strictly MANDATORY."
                }

        # 4. Financial Transfers / Chargebacks (Strictly Forbidden)
        if action_name in ["transfer_funds", "auto_refund", "FINANCIAL_TRANSFER"]:
            return {
                "action": action_name,
                "decision": "NEVER_EXECUTE",
                "allowed": False,
                "requires_approval": False,
                "approval_required": False,
                "risk_score": risk_score,
                "policy_version": self.config.policy_version,
                "authorization_scope": "FINANCIAL_MOVEMENT_FORBIDDEN",
                "reason": "Policy Guardrail PG-FIN-01: Autonomous financial movement is strictly prohibited by security architecture."
            }

        # 5. Case Creation / Alerting (Always permitted)
        if action_name in ["create_security_case", "alert_soc", "record_audit"]:
            return {
                "action": action_name,
                "decision": "AUTO_EXECUTE",
                "allowed": True,
                "requires_approval": False,
                "approval_required": False,
                "risk_score": risk_score,
                "policy_version": self.config.policy_version,
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
            "policy_version": self.config.policy_version,
            "authorization_scope": "UNKNOWN_SCOPE",
            "reason": f"Unclassified action '{action_name}' requires human approval."
        }
