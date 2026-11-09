import hashlib
import hmac


def verify_hmac_sha256(secret: str, payload: bytes, signature: str) -> bool:
    """
    Verifies the HMAC-SHA-256 signature of a payload using constant-time comparison.
    """
    if not secret or not signature:
        return False

    expected_hmac = hmac.new(
        key=secret.encode('utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_hmac, signature)
