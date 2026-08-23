from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class ExposureMatch(BaseModel):
    indicator: str
    indicator_type: str  # card_fingerprint, bin, email
    source_name: str
    exposure_type: str  # stealer_log, paste, dark_web_market, breach_dump
    confidence: float  # 0.0 to 1.0
    leak_date: str
    metadata: Dict[str, Any] = {}

class ThreatIntelProvider(ABC):
    """
    Abstract Threat Intelligence Provider interface.
    Decouples threat intel sources from the risk correlation engine.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
    
    @abstractmethod
    async def search_card_fingerprint(self, card_fingerprint: str) -> List[ExposureMatch]:
        """Search exposure feeds by HMAC-SHA256 card fingerprint."""
        pass
    
    @abstractmethod
    async def search_bin_exposure(self, bin_number: str) -> List[ExposureMatch]:
        """Search high-risk BIN breaches."""
        pass
    
    @abstractmethod
    async def search_email_exposure(self, email: str) -> List[ExposureMatch]:
        """Search customer email breaches."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider feed is available."""
        pass
