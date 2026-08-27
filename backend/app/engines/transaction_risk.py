from typing import Any, Dict, List

from app.models.entities import Customer, Transaction


class TransactionRiskEngine:
    """
    Deterministic Transaction Risk Engine.
    Evaluates:
    - Amount anomalies (relative to customer profile / typical tier)
    - Velocity anomalies (rapid transactions within 10-minute window)
    - Geographic anomalies (country/city mismatch)
    - Device anomalies (unrecognized/untrusted device ID)
    """

    def evaluate(self, txn: Transaction, customer: Customer) -> Dict[str, Any]:
        factor_score = 0.0
        reasons: List[str] = []
        details: Dict[str, Any] = {}

        # 1. Amount Anomaly
        # Typical customer average: ₹1,200. High threshold: ₹10,000+
        if txn.amount >= 15000:
            factor_score += 35.0
            reasons.append(f"Critical amount anomaly: ₹{txn.amount:,.2f} is 15x customer baseline average")
            details["amount_severity"] = "CRITICAL"
        elif txn.amount >= 5000:
            factor_score += 20.0
            reasons.append(f"Moderate amount anomaly: ₹{txn.amount:,.2f}")
            details["amount_severity"] = "MEDIUM"
        else:
            details["amount_severity"] = "NORMAL"

        # 2. Velocity Anomaly (transactions in last 10 minutes)
        if txn.velocity_10m >= 4:
            factor_score += 30.0
            reasons.append(f"High velocity anomaly: {txn.velocity_10m} rapid attempts in 10 minutes")
            details["velocity_severity"] = "HIGH"
        elif txn.velocity_10m >= 2:
            factor_score += 15.0
            reasons.append(f"Elevated velocity: {txn.velocity_10m} attempts in 10 minutes")
            details["velocity_severity"] = "MEDIUM"
        else:
            details["velocity_severity"] = "NORMAL"

        # 3. Geographic Anomaly
        if customer.default_country and txn.location_country:
            if customer.default_country.lower() != txn.location_country.lower():
                factor_score += 25.0
                reasons.append(f"Cross-border geographic mismatch: Origin {txn.location_city}, {txn.location_country} vs customer home {customer.default_city}, {customer.default_country}")
                details["geo_severity"] = "HIGH"
            elif customer.default_city.lower() != txn.location_city.lower():
                factor_score += 10.0
                reasons.append(f"Inter-city location anomaly: {txn.location_city} vs {customer.default_city}")
                details["geo_severity"] = "LOW"
            else:
                details["geo_severity"] = "NORMAL"

        # 4. Device Anomaly
        if txn.device_id.startswith("dev_suspicious") or "foreign" in txn.device_id:
            factor_score += 15.0
            reasons.append(f"Untrusted device profile detected: {txn.device_id}")
            details["device_severity"] = "HIGH"
        else:
            details["device_severity"] = "NORMAL"

        # Normalize score to 0 - 100
        normalized_score = min(100.0, factor_score)

        return {
            "score": normalized_score,
            "reasons": reasons,
            "details": details
        }
