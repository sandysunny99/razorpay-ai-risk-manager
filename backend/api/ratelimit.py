"""Per-client rate limiting for public ingest endpoints (SlowAPI, MIT).

The limit is read on every request from NETVRIO_RATE_LIMIT (default "300/minute") so operators
can tune it without a restart. Storage is in-process; behind several workers use a shared
backend (RATE_LIMIT_STORAGE_URI, e.g. redis://...). The client key is the socket peer address:
X-Forwarded-For is not trusted here, so put the WAF / reverse proxy in front and let it pass the
real peer (see docs/EDGE_SECURITY.md).
"""
import os

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

DEFAULT_LIMIT = "300/minute"


def ingest_limit() -> str:
    return os.getenv("NETVRIO_RATE_LIMIT", DEFAULT_LIMIT)


limiter = Limiter(key_func=get_remote_address, storage_uri=os.getenv("RATE_LIMIT_STORAGE_URI", "memory://"))


def rate_limit_exceeded(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"}, headers={"Retry-After": "60"})
