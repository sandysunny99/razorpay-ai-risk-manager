from enum import Enum
import hashlib
import hmac
import os


class ReferenceMode(str, Enum):
    TOKENIZED_REFERENCE = "TOKENIZED_REFERENCE"
    APPROVED_FINGERPRINT = "APPROVED_FINGERPRINT"
    MASKED_REFERENCE = "MASKED_REFERENCE"

class CardReferenceProtector:
    def __init__(self, allow_raw_reference: bool = False):
        self.allow_raw_reference = allow_raw_reference
        secret_hex = os.environ.get("FINGERPRINT_HMAC_SECRET")
        if secret_hex:
            self.secret = bytes.fromhex(secret_hex)
        else:
            self.secret = None

    def normalize(self, raw_reference: str, mode: ReferenceMode) -> str:
        if not raw_reference:
            raise ValueError("Reference cannot be empty")

        # Refuse obvious raw PANs in prod
        if not self.allow_raw_reference and len(raw_reference) in (15, 16, 19) and raw_reference.isdigit():
            raise ValueError("Raw PANs are strictly forbidden in production mode")

        if mode == ReferenceMode.TOKENIZED_REFERENCE:
            if not raw_reference.startswith("tok_") and not self.allow_raw_reference:
                raise ValueError("Expected a vault token, got raw value")
            return raw_reference

        elif mode == ReferenceMode.APPROVED_FINGERPRINT:
            if not self.secret:
                raise ValueError("Fingerprint mode requested but FINGERPRINT_HMAC_SECRET is missing")
            return "fp_" + hmac.new(self.secret, raw_reference.encode('utf-8'), hashlib.sha256).hexdigest()[:16]

        elif mode == ReferenceMode.MASKED_REFERENCE:
            if len(raw_reference) > 4:
                return f"****{raw_reference[-4:]}"
            return "****"

        raise ValueError("Unsupported reference mode")
