from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ActionDecision(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"
    QUARANTINE = "QUARANTINE"
    UNAVAILABLE = "UNAVAILABLE"

class RiskFactor(BaseModel):
    name: str
    description: str
    score_impact: float

class RiskEvidence(BaseModel):
    evidence_id: str
    source: str
    data: Dict[str, Any]
    timestamp: int

class RiskAssessment(BaseModel):
    risk_level: str
    risk_score: float = Field(..., ge=0.0, le=100.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_factors: List[RiskFactor]
    evidence_ids: List[str]
    correlation_id: str
    timestamp: int

class PolicyDecision(BaseModel):
    policy_id: str
    decision: ActionDecision
    reason_codes: List[str]
    evidence_ids: List[str]
    correlation_id: str
    timestamp: int

class RiskDecision(BaseModel):
    decision: ActionDecision
    policy_id: str
    risk_assessment: RiskAssessment
    evidence_ids: List[str]
    correlation_id: str
    timestamp: int
