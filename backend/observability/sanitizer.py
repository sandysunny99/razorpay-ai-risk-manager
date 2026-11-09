from typing import Any

# Forbidden keys (partial matches to be safe)
FORBIDDEN_KEYS = {
    "pan", "cvv", "pin", "authorization", "api_key", "webhook_secret",
    "token", "password", "raw_payload"
}

def sanitize_telemetry(data: Any) -> Any:
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            k_lower = k.lower()
            if any(forbidden in k_lower for forbidden in FORBIDDEN_KEYS):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_telemetry(v)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_telemetry(item) for item in data]
    else:
        return data
