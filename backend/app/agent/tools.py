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

class AgentToolRegistry:
    """
    Registry of specialized risk management tools exposed to the Agent.
    All sensitive actions are routed through policy guardrails and verification.
    """

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
        timeline: List[Dict[str, Any]]
    ) -> SecurityCase:
        case = SecurityCase(
            case_id=case_id,
            severity=severity,
            card_id=card_id,
            token_id=token_id,
            customer_id=customer_id,
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
            details=details
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
