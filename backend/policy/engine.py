import time
from typing import Optional

from backend.policy.models import MerchantPolicy, SecurityValidationResult
from backend.risk.models import ActionDecision, PolicyDecision, RiskAssessment


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

        # 2. Zombie Card Saver Overrides
        if zombie_remediation == ActionDecision.BLOCK:
            reason_codes.append("ZOMBIE_CARD_CRITICAL")
            return PolicyDecision(
                policy_id="zombie_pol_v1",
                decision=ActionDecision.BLOCK,
                reason_codes=reason_codes,
                evidence_ids=risk_assessment.evidence_ids,
                correlation_id=risk_assessment.correlation_id,
                timestamp=int(time.time())
            )
        elif zombie_remediation == ActionDecision.REVIEW and merchant_policy.require_step_up_for_zombie:
            reason_codes.append("ZOMBIE_CARD_REVIEW_REQUIRED")
            return PolicyDecision(
                policy_id="zombie_pol_v1",
                decision=ActionDecision.REVIEW,
                reason_codes=reason_codes,
                evidence_ids=risk_assessment.evidence_ids,
                correlation_id=risk_assessment.correlation_id,
                timestamp=int(time.time())
            )

        # 3. Standard Risk Scoring
        decision = ActionDecision.ALLOW
        if risk_assessment.risk_score >= merchant_policy.auto_block_threshold:
            decision = ActionDecision.BLOCK
            reason_codes.append("RISK_SCORE_EXCEEDS_BLOCK_THRESHOLD")
        elif risk_assessment.risk_score >= merchant_policy.auto_review_threshold:
            decision = ActionDecision.REVIEW
            reason_codes.append("RISK_SCORE_EXCEEDS_REVIEW_THRESHOLD")

        return PolicyDecision(
            policy_id="risk_pol_v1",
            decision=decision,
            reason_codes=reason_codes,
            evidence_ids=risk_assessment.evidence_ids,
            correlation_id=risk_assessment.correlation_id,
            timestamp=int(time.time())
        )
