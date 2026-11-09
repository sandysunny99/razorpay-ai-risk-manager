import contextvars
from typing import Optional

# Context variable to store the current tenant ID safely in async workflows
_tenant_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("tenant_id", default=None)

class TenantContext:
    """
    Context manager for enforcing tenant isolation.
    """
    def __init__(self, tenant_id: str):
        if not tenant_id:
            raise ValueError("Tenant ID must be provided")
        self.tenant_id = tenant_id
        self.token = None

    def __enter__(self):
        self.token = _tenant_id.set(self.tenant_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            _tenant_id.reset(self.token)

def get_current_tenant() -> Optional[str]:
    """Retrieves the currently active tenant ID."""
    return _tenant_id.get()
