from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.entities import Transaction, Card, PaymentToken, Customer, Merchant, SecurityCase, AuditEvent
from app.threat_intel.base import ThreatIntelProvider
from app.engines.transaction_risk import TransactionRiskEngine
from app.engines.card_risk import CardRiskEngine
from app.engines.token_risk import TokenRiskEngine
from app.engines.exposure_correlation import ExposureCorrelationEngine
from app.engines.risk_scorer import RiskScoringEngine
from app.engines.policy_engine import PolicyEngine
from app.engines.verification_engine import VerificationEngine
from app.integrations.razorpay_adapter import RazorpayPaymentAdapter

from app.engines.audit_ledger import AuditLedgerEngine

class ToolImpact:
    READ_ONLY = "READ_ONLY"
    LOW_IMPACT = "LOW_IMPACT"
    HIGH_IMPACT = "HIGH_IMPACT"
    CRITICAL = "CRITICAL"
    NEVER_EXECUTE = "NEVER_EXECUTE"

class AgentToolRegistry:
    """
    Registry of specialized risk management tools exposed to the Agent.
    All sensitive actions are strictly classified and gated by policy guardrails.
    """

    TOOL_SECURITY_CLASSIFICATIONS = {
        "get_transaction": ToolImpact.READ_ONLY,
        "get_card": ToolImpact.READ_ONLY,
        "get_token": ToolImpact.READ_ONLY,
        "get_customer": ToolImpact.READ_ONLY,
        "check_card_exposure": ToolImpact.READ_ONLY,
        "evaluate_transaction_risk": ToolImpact.READ_ONLY,
        "evaluate_card_risk": ToolImpact.READ_ONLY,
        "evaluate_token_risk": ToolImpact.READ_ONLY,
        "calculate_composite_risk": ToolImpact.READ_ONLY,
        "check_policy": ToolImpact.READ_ONLY,
        "create_case": ToolImpact.LOW_IMPACT,
        "write_audit": ToolImpact.LOW_IMPACT,
        "execute_revoke_token": ToolImpact.HIGH_IMPACT,
        "verify_and_recalculate": ToolImpact.HIGH_IMPACT,
        "suspend_card": ToolImpact.CRITICAL,
        "transfer_funds": ToolImpact.NEVER_EXECUTE,
    }

    def __init__(
        self,
        db: Session,
        threat_provider: ThreatIntelProvider,
        razorpay_adapter: RazorpayPaymentAdapter
    ):
        self.db = db
        self.threat_provider = threat_provider
        self.razorpay_adapter = razorpay_adapter
        
        self.txn_engine = TransactionRiskEngine()
        self.card_engine = CardRiskEngine()
        self.token_engine = TokenRiskEngine()
        self.exposure_engine = ExposureCorrelationEngine(threat_provider)
        self.risk_scorer = RiskScoringEngine()
        self.policy_engine = PolicyEngine()
        self.verification_engine = VerificationEngine(razorpay_adapter, self.risk_scorer)

    async def get_transaction(self, txn_id: str) -> Optional[Transaction]:
        return self.db.query(Transaction).filter(Transaction.txn_id == txn_id).first()

    async def get_card(self, card_id: str) -> Optional[Card]:
        return self.db.query(Card).filter(Card.card_id == card_id).first()

    async def get_token(self, token_id: str) -> Optional[PaymentToken]:
        return self.db.query(PaymentToken).filter(PaymentToken.token_id == token_id).first()

    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.customer_id == customer_id).first()

    async def check_card_exposure(self, card: Card, customer: Customer) -> Dict[str, Any]:
        return await self.exposure_engine.evaluate(card, customer)

    async def evaluate_transaction_risk(self, txn: Transaction, customer: Customer) -> Dict[str, Any]:
        return self.txn_engine.evaluate(txn, customer)

    async def evaluate_card_risk(self, card: Card) -> Dict[str, Any]:
        return self.card_engine.evaluate(card)

    async def evaluate_token_risk(self, token: Optional[PaymentToken], card: Card) -> Dict[str, Any]:
        return self.token_engine.evaluate(token, card)

    def calculate_composite_risk(
        self,
        txn_res: Dict[str, Any],
        exp_res: Dict[str, Any],
        crd_res: Dict[str, Any],
        tok_res: Dict[str, Any],
        customer_tier: str = "LOW"
    ) -> Dict[str, Any]:
        return self.risk_scorer.calculate(
            transaction_result=txn_res,
            exposure_result=exp_res,
            card_result=crd_res,
            token_result=tok_res,
            customer_risk_tier=customer_tier
        )

    def check_policy(self, action_name: str, risk_score: float, context: Dict[str, Any]) -> Dict[str, Any]:
        return self.policy_engine.evaluate_action(action_name, risk_score, context)

    async def execute_revoke_token(self, token_id: str, reason: str) -> Dict[str, Any]:
        return await self.razorpay_adapter.revoke_payment_token(token_id, reason)

    async def request_step_up_challenge(self, transaction_id: str, challenge_method: str = "SMS_OTP_SIMULATION") -> Dict[str, Any]:
        return await self.razorpay_adapter.request_step_up_challenge(transaction_id, challenge_method)

    async def verify_step_up_challenge(
        self,
        challenge_id: str,
        success: bool = True,
        outcome: Optional[str] = None
    ) -> Dict[str, Any]:
        return await self.razorpay_adapter.verify_step_up_challenge(challenge_id, success, outcome)

    def recalculate_after_step_up(
        self,
        txn_res: Dict[str, Any],
        exp_res: Dict[str, Any],
        crd_res: Dict[str, Any],
        tok_res: Dict[str, Any],
        customer_tier: str = "LOW",
        step_up_verified: bool = True,
        outcome: str = "SUCCESS"
    ) -> Dict[str, Any]:
        """
        Recalculates risk after 2FA step-up challenge verification.
        - SUCCESS: Damps transaction velocity/device friction (0.30x) while retaining external threat exposure signals.
        - FAILED: Escalates transaction risk score (+30.0) due to authentication mismatch.
        - TIMEOUT / ABANDONED: Retains elevated score and flags incomplete challenge status for SOC review.
        """
        adjusted_txn = dict(txn_res)
        normalized_outcome = outcome.upper()

        if normalized_outcome in ["SUCCESS", "VERIFIED"] and step_up_verified:
            adjusted_txn["score"] = max(0.0, adjusted_txn.get("score", 0.0) * 0.3)
            adjusted_txn["reasons"] = [r + " (2FA Step-Up Verified: Friction Damped)" for r in adjusted_txn.get("reasons", [])]
        elif normalized_outcome in ["FAILED", "INVALID_OTP"]:
            adjusted_txn["score"] = min(100.0, adjusted_txn.get("score", 0.0) + 30.0)
            adjusted_txn["reasons"] = [r + " (2FA Step-Up FAILED: Auth Mismatch)" for r in adjusted_txn.get("reasons", [])]
        elif normalized_outcome in ["TIMEOUT", "EXPIRED"]:
            adjusted_txn["reasons"] = [r + " (2FA Step-Up TIMEOUT: Verification Incomplete)" for r in adjusted_txn.get("reasons", [])]
        elif normalized_outcome in ["ABANDONED", "CANCELLED"]:
            adjusted_txn["reasons"] = [r + " (2FA Step-Up ABANDONED by Cardholder)" for r in adjusted_txn.get("reasons", [])]

        return self.risk_scorer.calculate(
            transaction_result=adjusted_txn,
            exposure_result=exp_res,
            card_result=crd_res,
            token_result=tok_res,
            customer_risk_tier=customer_tier
        )

    async def verify_and_recalculate(
        self,
        token: PaymentToken,
        card: Card,
        customer: Customer,
        transaction: Transaction,
        exposure_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        return await self.verification_engine.verify_token_revocation(
            token=token,
            card=card,
            customer=customer,
            transaction=transaction,
            exposure_result=exposure_result
        )

    def create_case(
        self,
        case_id: str,
        severity: str,
        card_id: str,
        token_id: Optional[str],
        customer_id: str,
        risk_score: float,
        reason: str,
        actions_taken: List[str],
        timeline: List[Dict[str, Any]],
        merchant_id: str = "mer_default_01"
    ) -> SecurityCase:
        case = SecurityCase(
            case_id=case_id,
            severity=severity,
            card_id=card_id,
            token_id=token_id,
            customer_id=customer_id,
            merchant_id=merchant_id,
            risk_score=risk_score,
            reason=reason,
            status="OPEN",
            assigned_to="SOC Tier 2 - Automated Risk Agent",
            actions_taken=actions_taken,
            timeline=timeline
        )
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case

    def write_audit(
        self,
        event_id: str,
        actor: str,
        decision: str,
        risk_score: float,
        policy: str,
        tool: str,
        action_requested: str,
        action_executed: str,
        verification: str,
        details: Dict[str, Any]
    ) -> AuditEvent:
        return AuditLedgerEngine.append_event(
            db=self.db,
            event_id=event_id,
            actor=actor,
            decision=decision,
            risk_score=risk_score,
            policy=policy,
            tool=tool,
            action_requested=action_requested,
            action_executed=action_executed,
            verification=verification,
            details=details
        )
