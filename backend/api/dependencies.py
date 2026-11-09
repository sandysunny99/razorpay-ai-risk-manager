from abc import ABC, abstractmethod
import os

from fastapi import HTTPException, Request


class TenantAuthProvider(ABC):
    @abstractmethod
    def authenticate(self, request: Request) -> str:
        pass

class TestTenantAuthProvider(TenantAuthProvider):
    def authenticate(self, request: Request) -> str:
        x_tenant = request.headers.get("x-tenant-id")
        if not x_tenant:
            raise HTTPException(status_code=401, detail="Missing tenant identification header (Test Mode)")
        return x_tenant

class ProductionTenantAuthProvider(TenantAuthProvider):
    def authenticate(self, request: Request) -> str:
        # Placeholder for real JWT / API_KEY auth
        # In a real environment, we'd validate a token here.
        raise HTTPException(status_code=501, detail="Production authentication not configured")

def get_tenant_auth_provider() -> TenantAuthProvider:
    auth_mode = os.environ.get("NETVRIO_TENANT_AUTH_MODE", "TEST")
    if auth_mode == "TEST" and os.environ.get("NETVRIO_ENV", "test") == "test":
        return TestTenantAuthProvider()
    return ProductionTenantAuthProvider()

def get_current_tenant(request: Request):
    # Dynamically resolve provider so environment config is checked at request time
    provider_instance = get_tenant_auth_provider()
    return provider_instance.authenticate(request)

def get_webhook_secret() -> str:
    secret = os.environ.get("WEBHOOK_SECRET")
    env = os.environ.get("NETVRIO_ENV", "test")
    if not secret:
        if env == "test":
            return "dummy_webhook_secret"
        raise HTTPException(status_code=500, detail="Server Configuration Error: Missing WEBHOOK_SECRET")
    return secret
