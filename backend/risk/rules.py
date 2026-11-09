from backend.risk.models import RiskFactor


def evaluate_amount(amount: float) -> RiskFactor:
    if amount > 100000:
        return RiskFactor(name="critical_amount", description="Transaction amount exceeds 100k", score_impact=95.0)
    if amount > 10000:
        return RiskFactor(name="high_amount", description="Transaction amount exceeds 10k", score_impact=50.0)
    return RiskFactor(name="normal_amount", description="Transaction amount is normal", score_impact=0.0)

def evaluate_velocity(velocity: int) -> RiskFactor:
    if velocity > 5:
        return RiskFactor(name="high_velocity", description="More than 5 transactions in 1h", score_impact=30.0)
    return RiskFactor(name="normal_velocity", description="Velocity is normal", score_impact=0.0)
