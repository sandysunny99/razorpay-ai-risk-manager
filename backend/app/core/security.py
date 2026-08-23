import hmac
import hashlib
import re
from typing import Optional
from app.core.config import settings

def luhn_checksum_valid(card_number: str) -> bool:
    """Validate a card number using Luhn algorithm."""
    digits = [int(c) for c in re.sub(r"\D", "", card_number)]
    if len(digits) < 13 or len(digits) > 19:
        return False
    
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = digit * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += digit
            
    return checksum % 10 == 0

def mask_pan(pan: str) -> str:
    """Mask a credit card PAN to PCI-aware format: **** **** **** 1234"""
    clean_pan = re.sub(r"\D", "", pan)
    if len(clean_pan) < 4:
        return "****"
    last_four = clean_pan[-4:]
    return f"**** **** **** {last_four}"

def extract_bin(pan: str) -> str:
    """Extract 6-digit Bank Identification Number (BIN)."""
    clean_pan = re.sub(r"\D", "", pan)
    if len(clean_pan) >= 6:
        return clean_pan[:6]
    return "000000"

def generate_card_fingerprint(pan: str, salt: Optional[str] = None) -> str:
    """
    Generate an HMAC-SHA256 cryptographic card fingerprint.
    Raw PAN is never stored or matched directly; fingerprinting enables
    zero-knowledge matching against exposed breach feeds.
    """
    clean_pan = re.sub(r"\D", "", pan)
    key = (salt or settings.HMAC_SECRET_KEY).encode("utf-8")
    h = hmac.new(key, clean_pan.encode("utf-8"), hashlib.sha256)
    return h.hexdigest()

CARD_REGEX = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b|\b\d{13,19}\b")

def redact_sensitive_data(text: str) -> str:
    """
    DLP Redaction: Scans arbitrary text/logs/payloads and replaces any
    potential credit card number with masked tokens.
    """
    def _replace_pan(match: re.Match) -> str:
        matched_str = match.group(0)
        digits = re.sub(r"\D", "", matched_str)
        if 13 <= len(digits) <= 19:
            return mask_pan(digits)
        return matched_str

    return CARD_REGEX.sub(_replace_pan, text)

def sanitize_untrusted_input(data: str) -> str:
    """
    Sanitize external threat intelligence content against prompt injection,
    HTML tags, and control characters before structured interpretation.
    """
    if not isinstance(data, str):
        return str(data)
    # Strip dangerous shell/control characters and HTML tags
    cleaned = re.sub(r"<[^>]*>", "", data)
    cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", cleaned)
    # Truncate overly long threat payloads to prevent context bloat
    return cleaned[:1000].strip()
