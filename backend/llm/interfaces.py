from abc import ABC, abstractmethod

from .health import ProviderHealth
from .schemas import RiskLLMRequest, RiskLLMResponse


class RiskLLMProvider(ABC):
    provider_name: str

    @abstractmethod
    def analyze(self, request: RiskLLMRequest, timeout: float = 5.0) -> RiskLLMResponse:
        pass

    @abstractmethod
    def health(self) -> ProviderHealth:
        pass
