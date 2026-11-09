
from pydantic import BaseModel


class MerchantPolicy(BaseModel):
    merchant_id: str
    auto_block_threshold: float
    auto_review_threshold: float
    require_step_up_for_zombie: bool

class SecurityValidationResult(BaseModel):
    is_valid_signature: bool
    is_idempotent: bool
    is_not_replayed: bool
    is_valid_tenant: bool
