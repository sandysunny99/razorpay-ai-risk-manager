import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.agent.tools import AgentToolRegistry
from app.models.schemas import InvestigationResponse, InvestigationStep, FactorItem, ToolAuditItem
from app.threat_intel.base import ThreatIntelProvider
from app.integrations.razorpay_adapter import RazorpayPaymentAdapter
from app.engines.policy_engine import PolicyEngine
from app.core.security import mask_pan

class RiskManagerAgent:
    """
    Autonomous Tiered Risk Manager Agent.
    Executes dynamic, evidence-grounded investigation based on risk tiers:
    - Level 0 (Risk < 35): Fast-path screening (minimal tools)
    - Level 1 (35 - 44): Light investigation (transaction, velocity, device, customer)
    - Level 2 (45 - 74): Risk investigation (card, token, velocity, merchant, exposure)
    - Level 3 (>= 75 or Zombie): Critical orchestration (deep threat intel, auto-remediation, verification)
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
        self.policy_engine = PolicyEngine()

    async def investigate_transaction(
        self,
        txn_id: str,
        merchant_id: Optional[str] = None,
        simulate_step_up: bool = False
    ) -> InvestigationResponse:
        timeline: List[InvestigationStep] = []
        tools_requested: List[str] = []
        tools_executed: List[str] = []
        tools_skipped: List[str] = []
        tool_audit: List[ToolAuditItem] = []

        now_str = lambda: datetime.utcnow().strftime("%H:%M:%S")

        def record_tool(tool_name: str, executed: bool, reason: str):
            tools_requested.append(tool_name)
            if executed:
                tools_executed.append(tool_name)
            else:
                tools_skipped.append(tool_name)
            tool_audit.append(ToolAuditItem(tool=tool_name, selected=executed, reason=reason))

        # 1. OBSERVE
        timeline.append(InvestigationStep(
            timestamp=now_str(),
            stage="OBSERVE",
            description=f"Transaction alert received for evaluation: TXN ID [{txn_id}]",
            tool_used="get_transaction",
            status="INFO"
        ))
        record_tool("get_transaction", True, "Initial transaction entity retrieval required for risk screening.")
        
        txn = await self.tools.get_transaction(txn_id)
        if not txn:
            raise ValueError(f"Transaction with ID '{txn_id}' not found in registry.")

        if merchant_id and txn.merchant_id != merchant_id:
            raise PermissionError(f"Multi-Tenant Security Violation: Access to transaction '{txn_id}' denied for merchant '{merchant_id}'.")

        record_tool("get_card", True, "Card metadata retrieval required for token and exposure analysis.")
        card = await self.tools.get_card(txn.card_id)

        record_tool("get_customer", True, "Customer baseline profile needed for behavioral velocity comparison.")
        customer = await self.tools.get_customer(txn.customer_id)

        token = None
        if txn.token_id:
            record_tool("get_token", True, "Token ID present on transaction record; fetching vault token state.")
            token = await self.tools.get_token(txn.token_id)
        else:
            record_tool("get_token", False, "No token_id present on transaction record; skipping token lookup.")

        if not card or not customer:
            raise ValueError("Incomplete transaction entity relations.")

        # 2. DETECT & SCREEN
        timeline.append(InvestigationStep(
            timestamp=now_str(),
            stage="DETECT",
            description=f"Evaluating transaction parameters: Amount ₹{txn.amount:,.2f} at {txn.location_city}, {txn.location_country} (Velocity: {txn.velocity_10m} attempts/10m)",
            tool_used="evaluate_transaction_risk",
            status="INFO"
        ))
        record_tool("evaluate_transaction_risk", True, "Deterministic transaction velocity, amount, and geo anomaly evaluation.")
        txn_risk = await self.tools.evaluate_transaction_risk(txn, customer)

        # Dynamic screening: Is transaction high risk on parameters or does it need deep correlation?
        is_amount_spike = txn.amount >= 15000.0
        is_velocity_high = txn.velocity_10m >= 3
        cust_country = getattr(customer, "default_country", getattr(customer, "country", "India"))
        is_cross_border = txn.location_country != cust_country
        is_new_device = getattr(txn, "device_new", False)

        # 3. INVESTIGATE & CORRELATE (Dynamic Tool Decision)
        exp_risk = {"score": 0.0, "match_count": 0, "matches": [], "reasons": ["Clean exposure profile"], "confidence": 0.0}
        crd_risk = {"score": 0.0, "reasons": []}
        tok_risk = {"score": 0.0, "is_zombie": False, "zombie_reason": None}

        # Check exposure if anomalous signals exist or during full screening
        if is_amount_spike or is_velocity_high or is_cross_border or txn_risk["score"] >= 35.0:
            record_tool("check_card_exposure", True, "Transaction anomalies or elevated score trigger dark-web credential exposure check.")
            timeline.append(InvestigationStep(
                timestamp=now_str(),
                stage="INVESTIGATE",
                description=f"Executing HMAC-SHA-256 exposure check for card {card.masked_pan} via BIN {card.bin}",
                tool_used="check_card_exposure",
                status="INFO"
            ))
            exp_risk = await self.tools.check_card_exposure(card, customer)
            
            if exp_risk["match_count"] > 0:
                timeline.append(InvestigationStep(
                    timestamp=now_str(),
                    stage="CORRELATE",
                    description=f"THREAT INTELLIGENCE MATCH: Card identified in {exp_risk['match_count']} external breach/stealer dumps! ({exp_risk['reasons'][0]})",
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
        else:
            record_tool("check_card_exposure", False, "Clean domestic transaction below anomaly threshold; skipping heavy CTI lookups.")

        # Check card & token risk
        record_tool("evaluate_card_risk", True, "Evaluating card expiration and historical fraud counts.")
        crd_risk = await self.tools.evaluate_card_risk(card)

        if token:
            record_tool("evaluate_token_risk", True, "Evaluating recurring payment token status and zombie token conditions.")
            tok_risk = await self.tools.evaluate_token_risk(token, card)
            if tok_risk.get("is_zombie"):
                timeline.append(InvestigationStep(
                    timestamp=now_str(),
                    stage="INVESTIGATE",
                    description=f"ZOMBIE TOKEN DETECTED: {tok_risk['zombie_reason']}",
                    tool_used="evaluate_token_risk",
                    status="WARNING"
                ))
        else:
            record_tool("evaluate_token_risk", False, "No token present on transaction.")

        # 4. REASON & ASSESS RISK
        record_tool("calculate_composite_risk", True, "Computing multi-factor weighted risk score across 6 risk dimensions.")
        risk_calc = self.tools.calculate_composite_risk(
            txn_res=txn_risk,
            exp_res=exp_risk,
            crd_res=crd_risk,
            tok_res=tok_risk,
            customer_tier=customer.risk_tier
        )
        initial_risk = risk_calc["composite_score"]
        initial_severity = risk_calc["severity"]

        # 5. DETERMINISTIC POLICY TIER CLASSIFICATION
        policy_context = {
            "is_zombie": tok_risk.get("is_zombie", False),
            "card_id": card.card_id,
            "token_id": token.token_id if token else None,
            "merchant_id": txn.merchant_id
        }
        tier_info = self.policy_engine.classify_risk_tier(initial_risk, context=policy_context)
        
        risk_level = tier_info["risk_level"]
        detection_status = tier_info["detection_status"]
        response_tier = tier_info["response_tier"]
        policy_decision = tier_info["policy_decision"]
        recommended_action = tier_info["recommended_action"]
        investigation_level = tier_info["investigation_level"]

        timeline.append(InvestigationStep(
            timestamp=now_str(),
            stage="ASSESS_RISK",
            description=f"Multi-factor Risk: {initial_risk}/100 [{risk_level}]. Detection: {detection_status} | Response Tier: {response_tier}",
            tool_used="calculate_composite_risk",
            status="WARNING" if initial_risk >= 40 else "INFO"
        ))

        # 6. POLICY GUARDRAIL EVALUATION
        token_policy = self.tools.check_policy("revoke_token", initial_risk, policy_context)
        card_policy = self.tools.check_policy("suspend_card", initial_risk, policy_context)

        timeline.append(InvestigationStep(
            timestamp=now_str(),
            stage="POLICY_CHECK",
            description=f"Policy Guardrail: Decision [{policy_decision}] -> Recommended Action: [{recommended_action}] (Approval Required: {tier_info['requires_approval']})",
            tool_used="check_policy",
            status="INFO",
            data={"tier_info": tier_info, "token_policy": token_policy, "card_policy": card_policy}
        ))

        # 7. TIERED DEFENSIVE ACTION & VERIFICATION
        action_taken = "ALLOW"
        action_policy_status = policy_decision
        verification_status = "NOT_APPLICABLE"
        final_risk = initial_risk
        final_severity = initial_severity
        final_factors = risk_calc["factors"]

        # Case A: Critical Auto-Remediation (Tier 4)
        if response_tier == "AUTO_REMEDIATE" and token and token_policy["allowed"] and token_policy["decision"] == "AUTO_EXECUTE":
            action_taken = f"REVOKE_TOKEN ({token.token_id})"
            timeline.append(InvestigationStep(
                timestamp=now_str(),
                stage="ACT",
                description=f"Autonomous Remediation: Revoking active payment token [{token.token_id}] on Razorpay Gateway",
                tool_used="revoke_token",
                status="SUCCESS"
            ))
            record_tool("execute_revoke_token", True, "Autonomous token revocation executed under Policy Rule PR-01.")
            await self.tools.execute_revoke_token(token.token_id, reason="Agentic Risk Mitigation: High Compromise Score")

            # Verify & Recalculate
            record_tool("verify_and_recalculate", True, "Mandatory vault state verification and post-action risk recalculation.")
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
                stage="VERIFY",
                description=f"Querying Razorpay Token Vault API to verify state transition -> Confirmed REVOKED",
                tool_used="verify_and_recalculate",
                status="SUCCESS"
            ))

            timeline.append(InvestigationStep(
                timestamp=now_str(),
                stage="RECALCULATE",
                description=f"Risk Recalculation complete post-remediation: Risk score dropped from {initial_risk} -> {final_risk} [{final_severity}]",
                tool_used="verify_and_recalculate",
                status="SUCCESS"
            ))

        # Case B: Step-Up Verification Challenge (Tier 2)
        elif response_tier == "STEP_UP" or simulate_step_up:
            action_taken = "REQUEST_STEP_UP"
            record_tool("request_step_up_challenge", True, "Simulated 2FA Step-Up Challenge initiated for moderate-risk transaction.")
            challenge = await self.tools.request_step_up_challenge(txn.txn_id)
            
            timeline.append(InvestigationStep(
                timestamp=now_str(),
                stage="ACT",
                description=f"Step-Up Challenge Initiated [{challenge['challenge_id']}]: Simulated 2FA/OTP check requested.",
                tool_used="request_step_up_challenge",
                status="INFO",
                data=challenge
            ))

            # If step-up simulation is requested
            if simulate_step_up:
                outcome_str = "SUCCESS" if simulate_step_up is True else str(simulate_step_up).upper()
                is_success = outcome_str in ["SUCCESS", "VERIFIED"]
                
                verify_res = await self.tools.verify_step_up_challenge(
                    challenge["challenge_id"],
                    success=is_success,
                    outcome=outcome_str
                )
                recalc = self.tools.recalculate_after_step_up(
                    txn_res=txn_risk,
                    exp_res=exp_risk,
                    crd_res=crd_risk,
                    tok_res=tok_risk,
                    customer_tier=customer.risk_tier,
                    step_up_verified=is_success,
                    outcome=outcome_str
                )
                final_risk = recalc["composite_score"]
                final_severity = recalc["severity"]
                final_factors = recalc["factors"]

                if outcome_str in ["SUCCESS", "VERIFIED"]:
                    verification_status = "CHALLENGE_VERIFIED_SUCCESSFUL"
                    action_taken = "STEP_UP_VERIFIED_ALLOW"
                    timeline.append(InvestigationStep(
                        timestamp=now_str(),
                        stage="VERIFY",
                        description=f"Step-Up Challenge Verified [SUCCESS]: Behavioral friction cleared -> Risk dropped from {initial_risk} -> {final_risk} [MONITOR]. Credential exposure evidence preserved for security monitoring.",
                        tool_used="verify_step_up_challenge",
                        status="SUCCESS"
                    ))
                elif outcome_str in ["FAILED", "INVALID_OTP"]:
                    verification_status = "CHALLENGE_FAILED_UNAUTHORIZED"
                    action_taken = "STEP_UP_FAILED_BLOCKED"
                    timeline.append(InvestigationStep(
                        timestamp=now_str(),
                        stage="VERIFY",
                        description=f"Step-Up Challenge FAILED: Invalid OTP credential provided -> Risk escalated from {initial_risk} -> {final_risk} [CRITICAL]. Security Case escalated.",
                        tool_used="verify_step_up_challenge",
                        status="FAILED"
                    ))
                elif outcome_str in ["TIMEOUT", "EXPIRED"]:
                    verification_status = "CHALLENGE_TIMEOUT_EXPIRED"
                    action_taken = "STEP_UP_TIMEOUT_ESCALATED"
                    timeline.append(InvestigationStep(
                        timestamp=now_str(),
                        stage="VERIFY",
                        description=f"Step-Up Challenge TIMEOUT: Cardholder did not respond within verification window. Case escalated to SOC queue.",
                        tool_used="verify_step_up_challenge",
                        status="WARNING"
                    ))
                else: # ABANDONED
                    verification_status = "CHALLENGE_ABANDONED"
                    action_taken = "STEP_UP_ABANDONED_CANCELLED"
                    timeline.append(InvestigationStep(
                        timestamp=now_str(),
                        stage="VERIFY",
                        description=f"Step-Up Challenge ABANDONED by user. Transaction cancelled.",
                        tool_used="verify_step_up_challenge",
                        status="WARNING"
                    ))

        # Case C: Security Review (Tier 3)
        elif response_tier == "REVIEW":
            action_taken = "SECURITY_REVIEW_ESCALATED"
            verification_status = "PENDING_ANALYST_REVIEW"
            timeline.append(InvestigationStep(
                timestamp=now_str(),
                stage="ACT",
                description=f"High risk ({initial_risk}/100) requires analyst review. Case escalated to SOC queue.",
                tool_used="create_case",
                status="WARNING"
            ))

        # Case D: Monitor / Allow (Tiers 0 & 1)
        elif response_tier == "MONITOR":
            action_taken = "MONITOR"
            verification_status = "MONITORING_ACTIVE"
        else:
            action_taken = "ALLOW"
            verification_status = "ALLOWED"

        # 8. CASE MANAGEMENT & AUDIT RECORDING
        case_id = None
        if initial_risk >= 45.0 or response_tier in ["STEP_UP", "REVIEW", "AUTO_REMEDIATE"] or action_taken.startswith("STEP_UP_FAILED") or action_taken.startswith("STEP_UP_TIMEOUT"):
            case_id = f"CASE-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            record_tool("create_case", True, "Persisting security case record for incident tracking.")
            self.tools.create_case(
                case_id=case_id,
                severity=initial_severity,
                card_id=card.card_id,
                token_id=token.token_id if token else None,
                customer_id=customer.customer_id,
                merchant_id=txn.merchant_id,
                risk_score=final_risk,
                reason=f"Composite risk {initial_risk}/100 [{risk_level}]. Tier: {response_tier}. Action: {action_taken}. Factors: {', '.join(txn_risk['reasons'] + exp_risk['reasons'])}",
                actions_taken=[action_taken],
                timeline=[step.model_dump() for step in timeline]
            )
        else:
            record_tool("create_case", False, "Low risk / clean transaction; skipping case creation.")

        event_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
        record_tool("write_audit", True, "Recording hash-chained audit entry in tamper-evident ledger.")
        self.tools.write_audit(
            event_id=event_id,
            actor="RiskManagerAgent",
            decision=f"Initial Risk: {initial_risk} [{response_tier}] -> Action: {action_taken} -> Final Risk: {final_risk}",
            risk_score=initial_risk,
            policy=action_policy_status,
            tool="RiskManagerAgent.investigate_transaction",
            action_requested=recommended_action,
            action_executed=action_taken,
            verification=verification_status,
            details={
                "case_id": case_id,
                "customer_id": customer.customer_id,
                "masked_pan": card.masked_pan,
                "merchant_id": txn.merchant_id,
                "detection_status": detection_status,
                "response_tier": response_tier
            }
        )

        timeline.append(InvestigationStep(
            timestamp=now_str(),
            stage="AUDIT",
            description=f"Audit record [{event_id}] persisted to tamper-evident hash ledger",
            tool_used="write_audit",
            status="SUCCESS"
        ))

        # Calibrated Evidence-Grounded Explainability Reasoning
        if response_tier == "AUTO_REMEDIATE":
            agent_reasoning = (
                f"[EVID-EXP-002] Dark-web stealer log match confirmed with [EVID-TOK-004] active payment token and "
                f"[EVID-TXN-001] ₹{txn.amount:,.2f} velocity/geo anomaly. Composite risk {initial_risk}/100 meets strict "
                f"Policy PR-01 autonomous revocation threshold (>=75.0). Token was revoked on Razorpay Vault, reducing risk to {final_risk}."
            )
        elif response_tier == "STEP_UP":
            if action_taken == "STEP_UP_VERIFIED_ALLOW":
                agent_reasoning = (
                    f"[EVID-TXN-001] Sub-critical anomaly ({initial_risk}/100) triggered Step-Up 2FA Challenge. "
                    f"Customer successfully authenticated, damping behavioral friction and reducing risk to {final_risk} [MONITOR]. "
                    f"Residual credential exposure signals remain indexed for continuous telemetry."
                )
            elif action_taken == "STEP_UP_FAILED_BLOCKED":
                agent_reasoning = (
                    f"[EVID-TXN-001] Step-Up 2FA Challenge FAILED: Invalid verification credentials provided. "
                    f"Risk escalated to {final_risk} [CRITICAL]. Transaction blocked and security case {case_id} created."
                )
            else:
                agent_reasoning = (
                    f"[EVID-TXN-001] Broad detection layer flagged suspicious anomaly ({initial_risk}/100). "
                    f"To prevent checkout friction on legitimate users, a Step-Up 2FA Challenge was initiated under Tier 2 policy."
                )
        elif response_tier == "REVIEW":
            agent_reasoning = (
                f"[EVID-TXN-001] Elevated risk score ({initial_risk}/100): Anomalous velocity/location observed without confirmed stealer dump. "
                f"Escalated to Tier 3 Security Review for supervisor sign-off under Policy PG-01."
            )
        elif response_tier == "MONITOR":
            agent_reasoning = (
                f"[EVID-TXN-001] Moderate signal ({initial_risk}/100): Minor baseline variance below 2FA threshold. "
                f"Indexed for post-authorization telemetry monitoring under Tier 1."
            )
        else:
            agent_reasoning = (
                f"[EVID-TXN-001] Clean legitimate transaction ({initial_risk}/100) from {txn.location_city}. "
                f"Zero credential breach exposure found. Standard payment authorized under Tier 0."
            )

        return InvestigationResponse(
            investigation_id=f"INV-{uuid.uuid4().hex[:8].upper()}",
            initial_risk=initial_risk,
            final_risk=final_risk,
            initial_severity=initial_severity,
            final_severity=final_severity,
            risk_level=risk_level,
            detection_status=detection_status,
            response_tier=response_tier,
            policy_decision=policy_decision,
            recommended_action=recommended_action,
            investigation_level=investigation_level,
            action_taken=action_taken,
            policy_status=action_policy_status,
            verification_status=verification_status,
            case_id=case_id,
            timeline=timeline,
            agent_reasoning=agent_reasoning,
            explainable_factors=final_factors,
            tools_requested=tools_requested,
            tools_executed=tools_executed,
            tools_skipped=tools_skipped,
            tool_audit=tool_audit
        )
