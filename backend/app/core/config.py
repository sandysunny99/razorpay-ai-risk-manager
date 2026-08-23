import os
from pydantic_settings import BaseSettings
from typing import Dict, Any

class Settings(BaseSettings):
    APP_NAME: str = "Razorpay Risk Manager Agent"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # Security Boundary Key for HMAC Card Fingerprinting
    HMAC_SECRET_KEY: str = "razorpay_risk_engine_hmac_secret_2026_salt_xyz987"
    
    # Database
    DATABASE_URL: str = "sqlite:///./risk_manager.db"
    
    # Dry Run Safety Guard
    DRY_RUN: bool = True
    
    # Razorpay Test Configuration
    RAZORPAY_KEY_ID: str = "rzp_test_mock_agent_key"
    RAZORPAY_KEY_SECRET: str = "rzp_test_mock_agent_secret"
    USE_MOCK_RAZORPAY: bool = True
    
    # Risk Scoring Weights (Configurable)
    WEIGHT_TRANSACTION: float = 25.0
    WEIGHT_EXPOSURE: float = 25.0
    WEIGHT_CARD: float = 15.0
    WEIGHT_TOKEN: float = 15.0
    WEIGHT_CUSTOMER: float = 10.0
    WEIGHT_MERCHANT: float = 10.0
    
    # Thresholds
    THRESHOLD_LOW: float = 25.0
    THRESHOLD_MEDIUM: float = 50.0
    THRESHOLD_HIGH: float = 75.0
    THRESHOLD_CRITICAL: float = 75.0
    
    # Policy Guardrails
    AUTO_REVOKE_TOKEN_ON_CRITICAL: bool = True
    AUTO_SUSPEND_CARD_ON_CRITICAL: bool = False  # Requires human review
    
    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
