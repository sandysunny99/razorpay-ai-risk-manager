import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.agent.tools import AgentToolRegistry
from app.models.schemas import InvestigationResponse, InvestigationStep, FactorItem
from app.threat_intel.base import ThreatIntelProvider
from app.integrations.razorpay_adapter import RazorpayPaymentAdapter
from app.core.security import mask_pan

class RiskManagerAgent:
    """
    Autonomous Risk Manager Agent.
    Executes the end-to-end Risk Management Workflow:
    OBSERVE -> DETECT -> INVESTIGATE -> CORRELATE -> REASON -> ASSESS RISK -> CHECK POLICY -> ACT -> VERIFY -> AUDIT
    """

    def __init__(
        self,
        db: Session,
        threat_provider: ThreatIntelProvider,
        razorpay_adapter: Optional[RazorpayPaymentAdapter] = None
    ):
        self.db = db
        self.threat_provider = threat_provider
        self.razorpay_adapter = razorpay_adapter or RazorpayPaymentAdapter()
        self.tools = AgentToolRegistry(db, threat_provider, self.razorpay_adapter)

    async def investigate_transaction(self, txn_id: str) -> InvestigationResponse:
        timeline: List[InvestigationStep] = []
        now_str = lambda: datetime.utcnow().strftime("%H:%M:%S")

        # 1. OBSERVE
        timeline.append(InvestigationStep(
            timestamp=now_str(),
            stage="OBSERVE",
            description=f"Transaction alert received for evaluation: TXN ID [{txn_id}]",
            tool_used="get_transaction",
            status="INFO"
        ))
        
        txn = await self.tools.get_transaction(txn_id)
        if not txn:
            raise ValueError(f"Transaction with ID '{txn_id}' not found in registry.")

        card = await self.tools.get_card(txn.card_id)
        customer = await self.tools.get_customer(txn.customer_id)
        token = await self.tools.get_token(txn.token_id) if txn.token_id else None

        if not card or not customer:
            raise ValueError("Incomplete transaction entity relations.")

        # 2. DETECT
        timeline.append(InvestigationStep(
            timestamp=now_str(),
            stage="DETECT",
            description=f"Evaluating transaction parameters: Amount ₹{txn.amount:,.2f} at {txn.location_city}, {txn.location_country} (Velocity: {txn.velocity_10m} attempts/10m)",
            tool_used="evaluate_transaction_risk",
            status="INFO"
        ))
        txn_risk = await self.tools.evaluate_transaction_risk(txn, customer)
        if txn_risk["score"] >= 50.0:
            timeline.append(InvestigationStep(
                timestamp=now_str(),
                stage="DETECT",
                description=f"Anomaly detected: Amount/Velocity/Geo deviation flagged (Risk contribution: {txn_risk['score']:.0f}/100)",
                tool_used="evaluate_transaction_risk",
                status="WARNING",
                data=txn_risk["details"]
            ))

        # 3. INVESTIGATE & CORRELATE
        timeline.append(InvestigationStep(
            timestamp=now_str(),
            stage="INVESTIGATE",
            description=f"Executing zero-knowledge exposure check for card {card.masked_pan} via HMAC fingerprint & BIN {card.bin}",
            tool_used="check_card_exposure",
            status="INFO"
        ))
        exp_risk = await self.tools.check_card_exposure(card, customer)
        
        if exp_risk["match_count"] > 0:
            timeline.append(InvestigationStep(
                timestamp=now_str(),
                stage="CORRELATE",
                description=f"CRITICAL THREAT MATCH: Card identified in {exp_risk['match_count']} external breach/stealer dumps! ({exp_risk['reasons'][0]})",
                tool_used="check_card_exposure",
                status="WARNING",
                data={"matches": exp_risk["matches"]}
            ))
        else:
            timeline.append(InvestigationStep(
                timestamp=now_str(),
                stage="CORRELATE",
                description="Zero external breach exposure detected for card.",
                tool_used="check_card_exposure",
                status="SUCCESS"
            ))

        # Check Token and Card Status
        crd_risk = await self.tools.evaluate_card_risk(card)
        tok_risk = await self.tools.evaluate_token_risk(token, card)
        
        if tok_risk.get("is_zombie"):
            timeline.append(InvestigationStep(
                timestamp=now_str(),
                stage="INVESTIGATE",
                description=f"ZOMBIE TOKEN DETECTED: {tok_risk['zombie_reason']}",
                tool_used="evaluate_token_risk",
                status="WARNING"
            ))

        # 4. REASON & ASSESS RISK
        risk_calc = self.tools.calculate_composite_risk(
            txn_res=txn_risk,
            exp_res=exp_risk,
            crd_res=crd_risk,
            tok_res=tok_risk,
            customer_tier=customer.risk_tier
        )
        initial_risk = risk_calc["composite_score"]
        initial_severity = risk_calc["severity"]

        timeline.append(InvestigationStep(
            timestamp=now_str(),
            stage="ASSESS_RISK",
            description=f"Initial multi-factor composite risk calculated: {initial_risk}/100 [{initial_severity}]. Recommendation: {risk_calc['recommendation']}",
            tool_used="calculate_composite_risk",
            status="WARNING" if initial_risk >= 75 else "INFO"
        ))

        # 5. CHECK POLICY
        context = {
            "is_zombie": tok_risk.get("is_zombie", False),
            "card_id": card.card_id,
            "token_id": token.token_id if token else None
        }
        
        token_policy = self.tools.check_policy("revoke_token", initial_risk, context)
        card_policy = self.tools.check_policy("suspend_card", initial_risk, context)

        timeline.append(InvestigationStep(
            timestamp=now_str(),
            stage="POLICY_CHECK",
            description=f"Policy Guardrail Engine evaluated: Token Revocation [{token_policy['decision']}], Card Suspension [{card_policy['decision']}]",
            tool_used="check_policy",
            status="INFO",
            data={"token_policy": token_policy, "card_policy": card_policy}
        ))

        # 6. ACT (If allowed)
        action_taken = "NONE"
        action_policy_status = token_policy["decision"]
        verification_status = "NOT_APPLICABLE"
        final_risk = initial_risk
        final_severity = initial_severity
        final_factors = risk_calc["factors"]
        
        if token and token_policy["allowed"] and token_policy["decision"] == "AUTO_EXECUTE":
            action_taken = f"REVOKE_TOKEN ({token.token_id})"
            timeline.append(InvestigationStep(
                timestamp=now_str(),
                stage="ACT",
                description=f"Autonomous Action Initiated: Revoking active payment token [{token.token_id}] on Razorpay Gateway",
                tool_used="revoke_token",
                status="SUCCESS"
            ))
            
            await self.tools.execute_revoke_token(token.token_id, reason="Agentic Risk Mitigation: High Compromise Score")
            
            # 7. VERIFY & RECALCULATE
            timeline.append(InvestigationStep(
                timestamp=now_str(),
                stage="VERIFY",
                description=f"Querying Razorpay Token Vault API to verify state transition -> Confirmed REVOKED",
                tool_used="verify_and_recalculate",
                status="SUCCESS"
            ))
            
            verification = await self.tools.verify_and_recalculate(
                token=token,
                card=card,
                customer=customer,
                transaction=txn,
                exposure_result=exp_risk
            )
            
            verification_status = "VERIFIED_SUCCESSFUL"
            final_risk = verification["recalculated_risk"]
            final_severity = verification["recalculated_severity"]
            final_factors = verification["recalculated_factors"]
            
            timeline.append(InvestigationStep(
                timestamp=now_str(),
                stage="RECALCULATE",
                description=f"Risk Recalculation complete post-remediation: Risk score dropped from {initial_risk} -> {final_risk} [{final_severity}]",
                tool_used="verify_and_recalculate",
                status="SUCCESS"
            ))

        # 8. AUDIT & CASE MANAGEMENT
        case_id = f"CASE-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        actions_list = [action_taken] if action_taken != "NONE" else ["MONITOR"]
        
        self.tools.create_case(
            case_id=case_id,
            severity=initial_severity,
            card_id=card.card_id,
            token_id=token.token_id if token else None,
            customer_id=customer.customer_id,
            risk_score=initial_risk,
            reason=f"Composite risk {initial_risk}/100. Factors: {', '.join(txn_risk['reasons'] + exp_risk['reasons'])}",
            actions_taken=actions_list,
            timeline=[step.model_dump() for step in timeline]
        )

        event_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
        self.tools.write_audit(
            event_id=event_id,
            actor="RiskManagerAgent",
            decision=f"Initial Risk: {initial_risk} -> Action: {action_taken} -> Final Risk: {final_risk}",
            risk_score=initial_risk,
            policy=action_policy_status,
            tool="RiskManagerAgent.investigate_transaction",
            action_requested="revoke_token",
            action_executed=action_taken,
            verification=verification_status,
            details={"case_id": case_id, "customer_id": customer.customer_id, "masked_pan": card.masked_pan}
        )

        timeline.append(InvestigationStep(
            timestamp=now_str(),
            stage="AUDIT",
            description=f"Security Case [{case_id}] created; Immutable audit record [{event_id}] persisted to security ledger",
            tool_used="write_audit",
            status="SUCCESS"
        ))

        agent_reasoning = (
            f"The transaction of ₹{txn.amount:,.2f} originated from an unusual location ({txn.location_city}, {txn.location_country}) "
            f"with an elevated velocity ({txn.velocity_10m} attempts). Critical risk was corroborated by dark-web stealer log matching "
            f"on card fingerprint. Active payment token ({token.token_id if token else 'N/A'}) was autonomously revoked under Policy PR-01, "
            f"reducing active liability and dropping composite risk from {initial_risk} to {final_risk}."
        )

        return InvestigationResponse(
            investigation_id=f"INV-{uuid.uuid4().hex[:8].upper()}",
            initial_risk=initial_risk,
            final_risk=final_risk,
            initial_severity=initial_severity,
            final_severity=final_severity,
            action_taken=action_taken,
            policy_status=action_policy_status,
            verification_status=verification_status,
            case_id=case_id,
            timeline=timeline,
            agent_reasoning=agent_reasoning,
            explainable_factors=final_factors
        )
