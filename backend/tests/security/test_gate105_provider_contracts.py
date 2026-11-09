import pytest

from backend.llm.health import ProviderHealthState
from backend.llm.providers.cloudflare import CloudflareProvider
from backend.llm.providers.grok import GrokProvider
from backend.llm.providers.huggingface import HuggingFaceProvider
from backend.llm.router import RiskLLMRouter


def test_provider_default_health_without_credentials_cf():
    provider = CloudflareProvider()
    assert provider.health().state == ProviderHealthState.NOT_VERIFIED  # Architectural change: missing credentials strictly maps to NOT_VERIFIED for health status

def test_provider_default_health_without_credentials_grok():
    provider = GrokProvider()
    assert provider.health().state == ProviderHealthState.NOT_VERIFIED  # Architectural change: missing credentials strictly maps to NOT_VERIFIED for health status

def test_provider_default_health_without_credentials_hf():
    provider = HuggingFaceProvider()
    assert provider.health().state == ProviderHealthState.NOT_VERIFIED  # Architectural change: missing credentials strictly maps to NOT_VERIFIED for health status

def test_provider_health_misconfigured_cf():
    provider = CloudflareProvider("fake_token")
    assert provider.health().state == ProviderHealthState.NOT_VERIFIED  # Architectural change: missing credentials strictly maps to NOT_VERIFIED for health status
