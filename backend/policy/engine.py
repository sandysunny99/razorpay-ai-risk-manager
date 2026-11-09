import time
from typing import Optional

from backend.policy.models import MerchantPolicy, SecurityValidationResult
from backend.risk.models import ActionDecision, PolicyDecision, RiskAssessment

_SEVERITY = {
    ActionDecision.ALLOW: 0,
    ActionDecision.REVIEW: 1,
    ActionDecision.QUARANTINE: 2,
    ActionDecision.BLOCK: 3,
}


class PolicyEngine:
    def __init__(self):
        pass

    def evaluate(
        self,
        risk_assessment: RiskAssessment,
        merchant_policy: MerchantPolicy,
        security_validation: SecurityValidationResult,
        zombie_remediation: Optional[ActionDecision] = None
    ) -> PolicyDecision:
        """
        The Policy Engine is the ONLY component allowed to convert risk evidence into an action.
        """
        reason_codes = []

        # 1. Hard Security Failures (Fail Closed)
        if not (security_validation.is_valid_signature and security_validation.is_idempotent and
                security_validation.is_not_replayed and security_validation.is_valid_tenant):
            reason_codes.append("SECURITY_VALIDATION_FAILED")
            return PolicyDecision(
                policy_id="sec_pol_v1",
                decision=ActionDecision.BLOCK,
                reason_codes=reason_codes,
                evidence_ids=risk_assessment.evidence_ids,
                correlation_id=risk_assessment.correlation_id,
                timestamp=int(time.time())
            )

        # 2. Standard Risk Scoring
        decision = ActionDecision.ALLOW
        policy_id = "risk_pol_v1"
        if risk_assessment.risk_score >= merchant_policy.auto_block_threshold:
            decision = ActionDecision.BLOCK
            reason_codes.append("RISK_SCORE_EXCEEDS_BLOCK_THRESHOLD")
        elif risk_assessment.risk_score >= merchant_policy.auto_review_threshold:
            decision = ActionDecision.REVIEW
            reason_codes.append("RISK_SCORE_EXCEEDS_REVIEW_THRESHOLD")

        # 3. Zombie Card Saver remediation can only make the outcome stricter, never more lenient.
        zombie_decision = None
        if zombie_remediation == ActionDecision.BLOCK:
            reason_codes.append("ZOMBIE_CARD_CRITICAL")
            zombie_decision = ActionDecision.BLOCK
        elif zombie_remediation == ActionDecision.REVIEW and merchant_policy.require_step_up_for_zombie:
            reason_codes.append("ZOMBIE_CARD_REVIEW_REQUIRED")
            zombie_decision = ActionDecision.REVIEW
        if zombie_decision is not None and _SEVERITY[zombie_decision] >= _SEVERITY[decision]:
            decision = zombie_decision
            policy_id = "zombie_pol_v1"

        return PolicyDecision(
            policy_id=policy_id,
            decision=decision,
            reason_codes=reason_codes,
            evidence_ids=risk_assessment.evidence_ids,
            correlation_id=risk_assessment.correlation_id,
            timestamp=int(time.time())
        )
