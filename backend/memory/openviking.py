from abc import ABC, abstractmethod
import os
from typing import Any, Dict, Optional


class MemoryProvider(ABC):
    @abstractmethod
    def store_context(self, tenant_id: str, case_id: str, data: Dict[str, Any], trust_level: str = "UNTRUSTED") -> None:
        pass
    @abstractmethod
    def retrieve_context(self, tenant_id: str, case_id: str) -> Optional[Dict[str, Any]]:
        pass

class InMemoryMemoryProvider(MemoryProvider):
    def __init__(self):
        self.store = {}
    def store_context(self, tenant_id: str, case_id: str, data: Dict[str, Any], trust_level: str = "UNTRUSTED") -> None:
        key = f"viking://{tenant_id}/investigations/{case_id}"
        self.store[key] = {"data": data, "trust_level": trust_level, "source": "system"}
    def retrieve_context(self, tenant_id: str, case_id: str) -> Optional[Dict[str, Any]]:
        return self.store.get(f"viking://{tenant_id}/investigations/{case_id}")

class OpenVikingMemoryProvider(MemoryProvider):
    def __init__(self):
        self.connection_string = os.environ.get("OPENVIKING_URL")
        self.is_available = bool(self.connection_string)

    def store_context(self, tenant_id: str, case_id: str, data: Dict[str, Any], trust_level: str = "UNTRUSTED") -> None:
        if not self.is_available:
            raise ConnectionError("OpenViking configuration unavailable. System UNAVAILABLE.")
        raise NotImplementedError("Real SDK not yet provided in environment")

    def retrieve_context(self, tenant_id: str, case_id: str) -> Optional[Dict[str, Any]]:
        if not self.is_available:
            raise ConnectionError("OpenViking configuration unavailable. System UNAVAILABLE.")
        raise NotImplementedError("Real SDK not yet provided in environment")

def get_memory_provider() -> MemoryProvider:
    if os.environ.get("NETVRIO_ENV") == "test":
        return InMemoryMemoryProvider()

    prov = OpenVikingMemoryProvider()
    if not prov.is_available:
        raise RuntimeError("OpenViking required in prod but unavailable.")
    return prov
