import secrets
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Razorpay AI Risk Manager Agent"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # ----------------------------------------------------------------
    # CORS — FIX C-01
    # Provide a comma-separated list of allowed origins via env var.
    # Defaults are dev-only. In production, set ALLOWED_ORIGINS explicitly.
    # ----------------------------------------------------------------
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:8000"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # ----------------------------------------------------------------
    # HMAC Secret — FIX C-02
    # No fallback string. If HMAC_SECRET_KEY is absent, generate a
    # random one at startup (demo-safe) and warn loudly.
    # In production, always set this via Render secret env var.
    # ----------------------------------------------------------------
    HMAC_SECRET_KEY: str = ""
    _ephemeral_secret: str | None = None

    @property
    def hmac_secret_resolved(self) -> str:
        if self.HMAC_SECRET_KEY:
            return self.HMAC_SECRET_KEY
        if self._ephemeral_secret is not None:
            return self._ephemeral_secret
        import warnings, secrets
        warnings.warn(
            "HMAC_SECRET_KEY not set — using ephemeral random key. Set HMAC_SECRET_KEY env var for stable production operation.",
            RuntimeWarning,
            stacklevel=2,
        )
        self._ephemeral_secret = secrets.token_hex(32)
        return self._ephemeral_secret

    # ----------------------------------------------------------------
    # API Auth Key — Phase 3
    # Optional in DRY_RUN / demo mode; required in production.
    # ----------------------------------------------------------------
    API_SECRET_KEY: str = ""

    # Database
    DATABASE_URL: str = "sqlite:///./risk_manager.db"

    # Dry Run Safety Guard
    DRY_RUN: bool = True

    # App mode (demo | production)
    APP_MODE: str = "demo"

    # Razorpay Test Configuration
    RAZORPAY_KEY_ID: str = "rzp_test_mock_agent_key"
    RAZORPAY_KEY_SECRET: str = "rzp_test_mock_agent_secret"
    RAZORPAY_WEBHOOK_SECRET: str = ""
    USE_MOCK_RAZORPAY: bool = True

    @property
    def razorpay_test_mode(self) -> bool:
        return self.RAZORPAY_KEY_ID.startswith("rzp_test_")

    @property
    def razorpay_configured(self) -> bool:
        return bool(
            self.RAZORPAY_KEY_ID
            and self.RAZORPAY_KEY_SECRET
            and not self.RAZORPAY_KEY_ID.startswith("rzp_test_mock")
        )

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
    THRESHOLD_HIGH: float = 60.0
    THRESHOLD_CRITICAL: float = 75.0

    # Policy Guardrails
    AUTO_REVOKE_TOKEN_ON_CRITICAL: bool = True
    AUTO_SUSPEND_CARD_ON_CRITICAL: bool = False  # Requires human review

    # ----------------------------------------------------------------
    # Free API Integrations (Phase 2) — all optional, graceful fallback
    # ----------------------------------------------------------------

    # Have I Been Pwned v3 — dark web breach correlation
    # Free key at: https://haveibeenpwned.com/API/Key
    HIBP_API_KEY: str = ""

    # AbuseIPDB — IP reputation scoring
    # Free at: https://abuseipdb.com (1,000 checks/day)
    ABUSEIPDB_API_KEY: str = ""

    # Upstash Redis — multi-worker safe rate limiting
    # Free at: https://upstash.com (10K req/day)
    REDIS_URL: str = ""

    # Sentry — production error monitoring
    # Free at: https://sentry.io (5K events/month)
    SENTRY_DSN: str = ""

    # ip-api.com — real geo-deviation scoring (no key, 45 req/min free)
    # Automatically used when transaction_ip is a public IP address.
    ENABLE_IP_GEO: bool = True

    @property
    def redis_configured(self) -> bool:
        return bool(self.REDIS_URL)

    @property
    def sentry_configured(self) -> bool:
        return bool(self.SENTRY_DSN)

    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
