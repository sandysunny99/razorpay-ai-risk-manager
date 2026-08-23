import re
from typing import Optional, Dict, Any

def mask_pan(pan: str) -> str:
    """
    Masks a credit card PAN to PCI-DSS compliant format: **** **** **** 4921
    Works with space-separated, hyphen-separated, or contiguous digits.
    """
    if not pan:
        return "**** **** **** ****"
    clean = re.sub(r"\D", "", str(pan))
    if len(clean) < 4:
        return "****"
    return f"**** **** **** {clean[-4:]}"

def mask_email(email: str) -> str:
    """Masks email address: john.doe@example.com -> j***e@example.com"""
    if not email or "@" not in email:
        return "u***@domain.com"
    parts = email.split("@", 1)
    username, domain = parts[0], parts[1]
    if len(username) <= 2:
        masked_user = username[0] + "***"
    else:
        masked_user = f"{username[0]}***{username[-1]}"
    return f"{masked_user}@{domain}"

def mask_phone(phone: str) -> str:
    """Masks phone number: +91 9876543210 -> +91 ******3210"""
    clean = re.sub(r"\D", "", str(phone or ""))
    if len(clean) < 4:
        return "****"
    return f"+** ******{clean[-4:]}"

def mask_ip(ip: str) -> str:
    """Masks IPv4 address: 122.166.45.10 -> 122.166.***.***"""
    if not ip or "." not in ip:
        return "***.***.***.***"
    octets = ip.split(".")
    if len(octets) == 4:
        return f"{octets[0]}.{octets[1]}.***.***"
    return "***.***.***.***"

def mask_customer_id(customer_id: str) -> str:
    """Masks customer ID: cust_544192 -> cust_***192"""
    cid = str(customer_id or "")
    if len(cid) <= 6:
        return cid
    return f"{cid[:5]}***{cid[-3:]}"

def mask_token(token_id: str) -> str:
    """Masks payment token: tok_live_12345678 -> tok_***5678"""
    tok = str(token_id or "")
    if len(tok) <= 8:
        return "tok_***"
    return f"{tok[:4]}***{tok[-4:]}"

def mask_api_key(api_key: str) -> str:
    """Masks API key: rzp_live_9a8b7c6d5e -> rzp_***5e"""
    key = str(api_key or "")
    if len(key) <= 6:
        return "key_***"
    return f"{key[:4]}***{key[-3:]}"

def mask_jwt(jwt_str: str) -> str:
    """Masks JWT string: eyJhbGciOi... -> eyJ***[JWT]"""
    jwt = str(jwt_str or "")
    if len(jwt) <= 10:
        return "[MASKED_JWT]"
    return f"{jwt[:6]}***[MASKED_JWT]"

def mask_secret(secret: str) -> str:
    """Masks arbitrary secret or password."""
    return "[REDACTED_SECRET]"

def mask_cloudflare_ray_id(ray_id: str) -> str:
    """Formats Ray ID for safe display: 8b3f12a9c0d4e5f6 -> 8b3f...e5f6"""
    r = str(ray_id or "")
    if len(r) <= 8:
        return r
    return f"{r[:4]}...{r[-4:]}"

class MaskingPolicy:
    """
    Role-aware dynamic masking policy engine.
    Default: DENY MORE DATA (Expose only minimally required fields).
    """
    @classmethod
    def apply(cls, data: Dict[str, Any], role: str = "ANALYST") -> Dict[str, Any]:
        masked = dict(data)
        if "card_number" in masked or "pan" in masked:
            pan_val = masked.pop("card_number", None) or masked.pop("pan", None)
            masked["masked_pan"] = mask_pan(pan_val)
        if "email" in masked and role != "SUPER_ADMIN":
            masked["email"] = mask_email(masked["email"])
        if "ip_address" in masked and role != "SUPER_ADMIN":
            masked["ip_address"] = mask_ip(masked["ip_address"])
        if "phone" in masked:
            masked["phone"] = mask_phone(masked["phone"])
        return masked
