from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class FactorItem(BaseModel):
    name: str
    weight: float
    score: float
    contribution: float
    reason: str

class RiskAssessmentResponse(BaseModel):
    assessment_id: str
    card_id: str
    token_id: Optional[str] = None
    transaction_id: Optional[str] = None
    composite_score: float
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    factors: List[FactorItem]
    recommendation: str
    calculated_at: datetime

class InvestigationRequest(BaseModel):
    transaction_id: Optional[str] = None
    card_id: Optional[str] = None
    token_id: Optional[str] = None
    customer_id: Optional[str] = None
    reason: Optional[str] = "Automated anomaly trigger"

class InvestigationStep(BaseModel):
    timestamp: str
    stage: str  # OBSERVE, DETECT, INVESTIGATE, CORRELATE, REASON, POLICY_CHECK, ACT, VERIFY, AUDIT
    description: str
    tool_used: Optional[str] = None
    status: str = "SUCCESS"  # SUCCESS, WARNING, FAILED, INFO
    data: Optional[Dict[str, Any]] = None

class ToolAuditItem(BaseModel):
    tool: str
    selected: bool
    reason: str

class InvestigationResponse(BaseModel):
    investigation_id: str
    initial_risk: float
    final_risk: float
    initial_severity: str
    final_severity: str
    risk_level: str = "LOW"
    detection_status: str = "CLEAN"  # CLEAN vs SUSPICIOUS
    response_tier: str = "LOW"  # LOW, MONITOR, STEP_UP, REVIEW, AUTO_REMEDIATE
    policy_decision: str = "ALLOW"  # ALLOW, MONITOR, STEP_UP_REQUIRED, REVIEW_REQUIRED, AUTO_EXECUTE, NEVER_EXECUTE
    recommended_action: str = "ALLOW"
    investigation_level: int = 0  # 0, 1, 2, 3
    action_taken: str
    policy_status: str
    verification_status: str
    case_id: Optional[str] = None
    timeline: List[InvestigationStep]
    agent_reasoning: str
    explainable_factors: List[FactorItem]
    tools_requested: List[str] = []
    tools_executed: List[str] = []
    tools_skipped: List[str] = []
    tool_audit: List[ToolAuditItem] = []

class StepUpChallengeRequest(BaseModel):
    transaction_id: str
    challenge_method: Optional[str] = "SMS_OTP_SIMULATION"

class StepUpChallengeResponse(BaseModel):
    challenge_id: str
    transaction_id: str
    status: str  # CHALLENGE_REQUIRED, VERIFIED, FAILED, EXPIRED
    challenge_method: str
    risk_before: float
    risk_after: Optional[float] = None
    response_tier_before: str
    response_tier_after: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    message: str

class CardResponse(BaseModel):
    card_id: str
    customer_id: str
    masked_pan: str
    bin: str
    cardholder_name: str
    expiry_month: int
    expiry_year: int
    is_expired: bool
    status: str
    failed_attempts: int
    previous_fraud_count: int
    active_token_count: int = 0
    exposure_count: int = 0
    current_risk_score: float = 0.0

class TokenResponse(BaseModel):
    token_id: str
    card_id: str
    customer_id: str
    merchant_id: str
    status: str
    token_age_days: int
    usage_count: int
    last_used_at: datetime
    is_zombie: bool = False
    zombie_reason: Optional[str] = None

class ZombieTokenAlert(BaseModel):
    token_id: str
    card_id: str
    masked_pan: str
    card_status: str
    is_card_expired: bool
    token_status: str
    last_used: str
    risk_level: str
    reason: str

class SecurityCaseResponse(BaseModel):
    case_id: str
    severity: str
    card_id: str
    token_id: Optional[str] = None
    customer_id: str
    merchant_id: str
    risk_score: float
    reason: str
    status: str
    assigned_to: str
    actions_taken: List[str]
    timeline: List[Dict[str, Any]]
    created_at: datetime

class AuditEventResponse(BaseModel):
    event_id: str
    actor: str
    agent_decision: str
    risk_score: float
    policy_evaluated: str
    tool_used: Optional[str]
    action_requested: Optional[str]
    action_executed: Optional[str]
    verification_result: Optional[str]
    details: Dict[str, Any]
    created_at: datetime

class OverviewMetrics(BaseModel):
    cards_monitored: int
    tokens_monitored: int
    active_zombie_tokens: int
    high_risk_cards: int
    critical_incidents: int
    exposure_events_count: int
    open_cases_count: int
    system_status: str
    dry_run_mode: bool
