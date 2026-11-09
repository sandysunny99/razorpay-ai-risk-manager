from enum import Enum


class ProviderHealthState(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    MISCONFIGURED = "MISCONFIGURED"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"
    NOT_VERIFIED = "NOT_VERIFIED"

class ProviderHealth:
    def __init__(self, provider_name: str, state: ProviderHealthState, details: str = ""):
        self.provider_name = provider_name
        self.state = state
        self.details = details
