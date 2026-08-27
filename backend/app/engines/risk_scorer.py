from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.models.schemas import FactorItem


class RiskScoringEngine:
    """
    Mathematical Composite Risk Scoring Engine.
    Computes explainable, weighted composite risk score (0 - 100)
    from 6 distinct risk dimensions.
    """

    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        self.weights = {
            "transaction": settings.WEIGHT_TRANSACTION,
            "exposure": settings.WEIGHT_EXPOSURE,
            "card": settings.WEIGHT_CARD,
            "token": settings.WEIGHT_TOKEN,
            "customer": settings.WEIGHT_CUSTOMER,
            "merchant": settings.WEIGHT_MERCHANT,
        }
        if custom_weights:
            self.weights.update(custom_weights)

    def calculate(
        self,
        transaction_result: Dict[str, Any],
        exposure_result: Dict[str, Any],
        card_result: Dict[str, Any],
        token_result: Dict[str, Any],
        customer_risk_tier: str = "LOW",
        merchant_risk_tier: str = "LOW"
    ) -> Dict[str, Any]:
        # Dimension raw scores (0 - 100)
        txn_score = float(transaction_result.get("score", 0.0))
        exp_score = float(exposure_result.get("score", 0.0))
        crd_score = float(card_result.get("score", 0.0))
        tok_score = float(token_result.get("score", 0.0))

        cust_score = 75.0 if customer_risk_tier == "HIGH" else (35.0 if customer_risk_tier == "MEDIUM" else 0.0)
        merch_score = 50.0 if merchant_risk_tier == "HIGH" else 0.0

        # Weighted calculation
        total_weight = sum(self.weights.values())

        contrib_txn = (txn_score * self.weights["transaction"]) / total_weight
        contrib_exp = (exp_score * self.weights["exposure"]) / total_weight
        contrib_crd = (crd_score * self.weights["card"]) / total_weight
        contrib_tok = (tok_score * self.weights["token"]) / total_weight
        contrib_cust = (cust_score * self.weights["customer"]) / total_weight
        contrib_merch = (merch_score * self.weights["merchant"]) / total_weight

        raw_composite = contrib_txn + contrib_exp + contrib_crd + contrib_tok + contrib_cust + contrib_merch

        # Boost to CRITICAL if multiple high-risk factors coincide
        # (e.g. Card Exposure + Active Token + Transaction Anomaly)
        if exp_score >= 80.0 and tok_score >= 15.0 and txn_score >= 50.0:
            raw_composite = max(raw_composite, 94.0)

        composite_score = round(min(100.0, max(0.0, raw_composite)), 1)

        # Severity Classification
        if composite_score >= settings.THRESHOLD_CRITICAL:
            severity = "CRITICAL"
        elif composite_score >= settings.THRESHOLD_MEDIUM:
            severity = "HIGH" if composite_score >= 60.0 else "MEDIUM"
        else:
            severity = "LOW"

        # Structured Factors
        factors: List[FactorItem] = [
            FactorItem(
                name="Threat & Breach Exposure",
                weight=self.weights["exposure"],
                score=exp_score,
                contribution=round(contrib_exp, 1),
                reason=" | ".join(exposure_result.get("reasons", ["No exposure"]))
            ),
            FactorItem(
                name="Transaction Anomalies",
                weight=self.weights["transaction"],
                score=txn_score,
                contribution=round(contrib_txn, 1),
                reason=" | ".join(transaction_result.get("reasons", ["Normal transaction velocity and amount"]))
            ),
            FactorItem(
                name="Card Status & Lifecycle",
                weight=self.weights["card"],
                score=crd_score,
                contribution=round(contrib_crd, 1),
                reason=" | ".join(card_result.get("reasons", ["Valid active card"]))
            ),
            FactorItem(
                name="Payment Token State",
                weight=self.weights["token"],
                score=tok_score,
                contribution=round(contrib_tok, 1),
                reason=" | ".join(token_result.get("reasons", ["No token anomalies"]))
            ),
            FactorItem(
                name="Customer Profile History",
                weight=self.weights["customer"],
                score=cust_score,
                contribution=round(contrib_cust, 1),
                reason=f"Customer risk tier: {customer_risk_tier}"
            ),
            FactorItem(
                name="Merchant Baseline Risk",
                weight=self.weights["merchant"],
                score=merch_score,
                contribution=round(contrib_merch, 1),
                reason=f"Merchant risk tier: {merchant_risk_tier}"
            )
        ]

        # Recommendation generation
        if severity == "CRITICAL":
            recommendation = "CRITICAL ACTION REQUIRED: Immediate payment token revocation permitted by policy. Card suspension requires human supervisor approval."
        elif severity == "HIGH":
            recommendation = "HIGH RISK: Trigger 2FA step-up challenge or escalate to SOC risk analyst for expedited review."
        elif severity == "MEDIUM":
            recommendation = "MEDIUM RISK: Flag transaction for enhanced post-authorization monitoring."
        else:
            recommendation = "LOW RISK: Standard authorization permitted."

        return {
            "composite_score": composite_score,
            "severity": severity,
            "factors": factors,
            "recommendation": recommendation
        }
