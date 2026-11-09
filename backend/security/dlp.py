import re
from typing import Any, Dict, List, Union

# Patterns for sensitive fields
SENSITIVE_KEYS = re.compile(r'pan|cvv|pin|password|secret|token|api_key|authorization', re.IGNORECASE)

def redact_sensitive_data(data: Union[Dict[str, Any], List[Any], str]) -> Union[Dict[str, Any], List[Any], str]:
    """
    Recursively redacts sensitive fields before logging or sending data to an LLM.
    """
    if isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            if SENSITIVE_KEYS.search(key):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_sensitive_data(value)
        return redacted
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    else:
        return data
