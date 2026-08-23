import re
from typing import Dict, Any, List, Tuple
from app.core.security import luhn_checksum_valid, mask_pan

# Regex patterns for sensitive candidate tokens
PAN_CANDIDATE_REGEX = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b|\b\d{13,19}\b")
BEARER_TOKEN_REGEX = re.compile(r"Bearer\s+([A-Za-z0-9\-\._~\+\/]+=*)", re.IGNORECASE)
JWT_REGEX = re.compile(r"\beyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\b")
API_KEY_REGEX = re.compile(r"\b(?:rzp|cf|sk|pk)_(?:live|test)_[a-zA-Z0-9]{10,32}\b", re.IGNORECASE)
DB_CONN_REGEX = re.compile(r"(?:sqlite|postgresql|mysql|mongodb)(?:\+[a-z]+)?://[^\s\"']+", re.IGNORECASE)
PRIVATE_KEY_REGEX = re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA )?PRIVATE KEY-----")

class DLPEngine:
    """
    Enterprise Data Loss Prevention (DLP) Gate.
    Proactively scans, redacts, and blocks raw credit card numbers, secrets, and auth tokens.
    """
    @classmethod
    def scan_for_violations(cls, data: Any) -> List[Dict[str, str]]:
        """
        Inspects strings, dictionaries, or lists and returns a list of detected DLP violations.
        """
        violations = []
        text_repr = str(data)

        # 1. PAN / Credit Card check with Luhn verification
        for match in PAN_CANDIDATE_REGEX.finditer(text_repr):
            digits = re.sub(r"\D", "", match.group(0))
            if 13 <= len(digits) <= 19 and luhn_checksum_valid(digits):
                violations.append({
                    "type": "PAN_DETECTED",
                    "severity": "CRITICAL",
                    "sample": mask_pan(digits),
                    "description": "Raw credit card PAN detected with valid Luhn checksum."
                })

        # 2. JWT Tokens
        if JWT_REGEX.search(text_repr):
            violations.append({
                "type": "JWT_TOKEN_DETECTED",
                "severity": "HIGH",
                "sample": "[REDACTED_JWT]",
                "description": "JWT authentication token detected in payload."
            })

        # 3. API Keys (Razorpay, Cloudflare, etc.)
        if API_KEY_REGEX.search(text_repr):
            violations.append({
                "type": "API_KEY_DETECTED",
                "severity": "HIGH",
                "sample": "[REDACTED_API_KEY]",
                "description": "API credential key detected in payload."
            })

        # 4. Database Connection Strings
        if DB_CONN_REGEX.search(text_repr):
            violations.append({
                "type": "DB_CONNECTION_DETECTED",
                "severity": "CRITICAL",
                "sample": "[REDACTED_DB_URI]",
                "description": "Database connection string with credentials detected."
            })

        # 5. Private Keys
        if PRIVATE_KEY_REGEX.search(text_repr):
            violations.append({
                "type": "PRIVATE_KEY_DETECTED",
                "severity": "CRITICAL",
                "sample": "[REDACTED_PRIVATE_KEY]",
                "description": "Asymmetric private key header detected."
            })

        return violations

    @classmethod
    def redact(cls, text: str) -> str:
        """
        Redacts all sensitive PANs, secrets, and auth tokens from text.
        Safe for use in loggers, telemetry, and external LLM contexts.
        """
        if not isinstance(text, str):
            text = str(text)

        # 1. Replace Luhn-valid PANs with masked format
        def _replace_pan(match: re.Match) -> str:
            digits = re.sub(r"\D", "", match.group(0))
            if 13 <= len(digits) <= 19 and luhn_checksum_valid(digits):
                return mask_pan(digits)
            return match.group(0)

        cleaned = PAN_CANDIDATE_REGEX.sub(_replace_pan, text)

        # 2. Redact secrets
        cleaned = JWT_REGEX.sub("[REDACTED_JWT]", cleaned)
        cleaned = API_KEY_REGEX.sub("[REDACTED_API_KEY]", cleaned)
        cleaned = BEARER_TOKEN_REGEX.sub("Bearer [REDACTED_TOKEN]", cleaned)
        cleaned = DB_CONN_REGEX.sub("[REDACTED_DB_URI]", cleaned)
        cleaned = PRIVATE_KEY_REGEX.sub("[REDACTED_PRIVATE_KEY]", cleaned)

        return cleaned
