from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.core.database import Base


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    risk_policy = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    email = Column(String(128), index=True, nullable=False)
    risk_tier = Column(String(32), default="LOW")
    default_country = Column(String(64), default="India")
    default_city = Column(String(64), default="Bengaluru")
    previous_chargebacks = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(String(64), unique=True, index=True, nullable=False)
    customer_id = Column(String(64), ForeignKey("customers.customer_id"), nullable=False)
    masked_pan = Column(String(32), nullable=False)  # e.g. **** **** **** 4921
    card_fingerprint = Column(String(64), unique=True, index=True, nullable=False)  # HMAC-SHA256
    bin = Column(String(8), index=True, nullable=False)  # First 6 digits
    cardholder_name = Column(String(128), nullable=False)
    expiry_month = Column(Integer, nullable=False)
    expiry_year = Column(Integer, nullable=False)
    is_expired = Column(Boolean, default=False)
    status = Column(String(32), default="ACTIVE")  # ACTIVE, SUSPENDED, BLOCKED, EXPIRED
    failed_attempts = Column(Integer, default=0)
    previous_fraud_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PaymentToken(Base):
    __tablename__ = "payment_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(String(64), unique=True, index=True, nullable=False)
    card_id = Column(String(64), ForeignKey("cards.card_id"), nullable=False)
    customer_id = Column(String(64), ForeignKey("customers.customer_id"), nullable=False)
    merchant_id = Column(String(64), default="DemoStore")
    status = Column(String(32), default="ACTIVE")  # ACTIVE, REVOKED, SUSPENDED, ROTATED
    token_age_days = Column(Integer, default=15)
    usage_count = Column(Integer, default=1)
    last_used_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    txn_id = Column(String(64), unique=True, index=True, nullable=False)
    customer_id = Column(String(64), ForeignKey("customers.customer_id"), nullable=False)
    card_id = Column(String(64), ForeignKey("cards.card_id"), nullable=False)
    token_id = Column(String(64), nullable=True)
    merchant_id = Column(String(64), default="DemoStore")
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    status = Column(String(32), default="PENDING")  # PENDING, SUCCESS, FLAGGED, BLOCKED, REFUNDED
    ip_address = Column(String(64), default="127.0.0.1")
    location_city = Column(String(64), default="Bengaluru")
    location_country = Column(String(64), default="India")
    device_id = Column(String(64), default="dev_trusted_01")
    velocity_10m = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class ThreatSource(Base):
    __tablename__ = "threat_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, nullable=False)
    source_type = Column(String(64), default="stealer_log")  # dark_web, breach_dump, stealer_log, paste
    reliability_score = Column(Float, default=0.90)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ExposureEvent(Base):
    __tablename__ = "exposure_events"

    id = Column(Integer, primary_key=True, index=True)
    card_fingerprint = Column(String(64), index=True, nullable=False)
    bin = Column(String(8), index=True, nullable=False)
    source_name = Column(String(128), nullable=False)
    exposure_type = Column(String(64), default="stealer_log")
    confidence_score = Column(Float, default=0.95)
    leak_date = Column(DateTime, default=datetime.utcnow)
    raw_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(String(64), unique=True, index=True, nullable=False)
    transaction_id = Column(String(64), nullable=True)
    card_id = Column(String(64), nullable=False)
    token_id = Column(String(64), nullable=True)
    composite_score = Column(Float, nullable=False)  # 0 to 100
    severity = Column(String(32), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    factor_breakdown = Column(JSON, default=dict)
    recommendation = Column(Text, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)

class SecurityCase(Base):
    __tablename__ = "security_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), unique=True, index=True, nullable=False)
    severity = Column(String(32), default="CRITICAL")
    card_id = Column(String(64), nullable=False)
    token_id = Column(String(64), nullable=True)
    customer_id = Column(String(64), nullable=False)
    merchant_id = Column(String(64), default="DemoStore")
    risk_score = Column(Float, default=0.0)
    reason = Column(Text, nullable=False)
    status = Column(String(32), default="OPEN")  # OPEN, INVESTIGATING, RESOLVED, DISMISSED
    assigned_to = Column(String(64), default="SOC Tier 2 - Automated Risk Agent")
    actions_taken = Column(JSON, default=list)
    timeline = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    actor = Column(String(64), default="RiskManagerAgent")
    agent_decision = Column(Text, nullable=False)
    risk_score = Column(Float, nullable=False, index=True)
    policy_evaluated = Column(String(64), nullable=False)
    tool_used = Column(String(64), nullable=True)
    action_requested = Column(String(64), nullable=True)
    action_executed = Column(String(64), nullable=True)
    verification_result = Column(String(64), nullable=True)
    previous_hash = Column(String(64), nullable=False, default="0" * 64)
    current_hash = Column(String(64), nullable=False, index=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class CloudflareSecurityEvent(Base):
    __tablename__ = "cloudflare_security_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    ray_id = Column(String(64), index=True, nullable=False)
    masked_ray_id = Column(String(32), nullable=False)
    tenant_id = Column(String(64), default="DemoStore", index=True)
    event_type = Column(String(64), default="WAF_INSPECT")  # WAF_BLOCK, BOT_CHALLENGE, RATE_LIMIT, WAF_INSPECT
    origin_ip = Column(String(64), default="122.166.45.10")
    country = Column(String(8), default="IN")
    waf_action = Column(String(32), default="ALLOW")  # ALLOW, BLOCK, CHALLENGE, LOG
    bot_score = Column(Integer, default=85)
    bot_signal = Column(String(64), default="HUMAN_TRAFFIC")
    rate_limit_signal = Column(String(32), default="ALLOW")
    tls_version = Column(String(16), default="TLSv1.3")
    edge_status = Column(String(32), default="NORMAL")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class DLPEvent(Base):
    __tablename__ = "dlp_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    violation_type = Column(String(64), nullable=False)  # PAN_DETECTED, JWT_DETECTED, API_KEY_DETECTED
    severity = Column(String(32), default="HIGH")  # HIGH, CRITICAL
    action_taken = Column(String(32), default="MASKED")  # MASKED, BLOCKED, REDACTED
    source_context = Column(String(128), default="API_INPUT")  # API_INPUT, AGENT_IO, LOG_PIPELINE
    masked_sample = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class KeyMetadata(Base):
    __tablename__ = "key_metadata"

    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String(64), unique=True, index=True, nullable=False)
    version = Column(String(16), nullable=False)
    algorithm = Column(String(32), default="AES-256-GCM")
    status = Column(String(32), default="ACTIVE")  # ACTIVE, RETIRED, REVOKED
    created_at = Column(DateTime, default=datetime.utcnow)

