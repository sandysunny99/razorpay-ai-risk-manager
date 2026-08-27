from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ZombieCardStatus(str, Enum):
    HEALTHY = "HEALTHY"
    AT_RISK = "AT_RISK"
    ZOMBIE = "ZOMBIE"
    CRITICAL = "CRITICAL"
    RESOLVED = "RESOLVED"

class ZombieSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ZombieActionType(str, Enum):
    MONITOR = "MONITOR"
    REQUEST_STEP_UP = "REQUEST_STEP_UP"
    REVIEW = "REVIEW"
    REVOKE_TOKEN = "REVOKE_TOKEN"
    REPLACE_TOKEN = "REPLACE_TOKEN"
    RELINK_TOKEN = "RELINK_TOKEN"

class DependentTokenItem(BaseModel):
    token_id: str
    merchant_id: str
    merchant_name: str
    status: str
    last_used_at: Optional[str] = None
    created_at: Optional[str] = None
    transaction_count: int = 0
    is_recurring: bool = False
    token_health: str = "Healthy"
    risk_score: float = 0.0
    recommended_action: ZombieActionType = ZombieActionType.MONITOR

class ZombieCardSummary(BaseModel):
    card_id: str
    card_fingerprint: str
    masked_pan: str
    card_state: str
    expiration_date: Optional[str] = None
    time_since_state_change: str
    active_token_count: int
    total_token_count: int
    zombie_status: ZombieCardStatus
    severity: ZombieSeverity
    authoritative_risk_score: float
    recommended_action: ZombieActionType
    affected_merchant_count: int
    recurring_subscription_count: int
    exposure_detected: bool = False

class ZombieStatisticsResponse(BaseModel):
    total_zombie_cards: int
    active_zombie_tokens: int
    critical_zombies: int
    recently_used_zombies: int
    exposure_linked_zombies: int
    tokens_saved: int
    tokens_revoked: int
    pending_reviews: int
    step_up_challenges: int
    verification_success_rate: float

class ZombieAnalysisResponse(BaseModel):
    card: ZombieCardSummary
    dependent_tokens: List[DependentTokenItem]
    recent_transactions: List[Dict[str, Any]]
    merchant_impact: Dict[str, Any]
    customer_impact: Dict[str, Any]
    policy_tier: str
    audit_hash: str
