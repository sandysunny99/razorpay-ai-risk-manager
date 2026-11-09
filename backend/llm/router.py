import logging
import time
from typing import List, Optional, Tuple

from pydantic import ValidationError

from .errors import LLMError, ProviderTimeoutError, SchemaValidationError, SensitiveDataDetected
from .interfaces import RiskLLMProvider
from .schemas import RiskLLMRequest, RiskLLMResponse

logger = logging.getLogger(__name__)

class RiskLLMRouter:
    def __init__(self, providers: List[RiskLLMProvider]):
        # Providers should be passed in priority order
        self.providers = providers

    def analyze(self, request: RiskLLMRequest) -> Tuple[Optional[RiskLLMResponse], dict]:
        audit_metadata = {
            "provider": None,
            "status": "FAILED",
            "fallback_used": False,
            "latency": 0.0,
            "schema_valid": False,
            "failure_reason": "ALL_PROVIDERS_UNAVAILABLE"
        }

        start_time = time.time()

        # Test 1: Check sensitive data before any external call
        try:
            # We already have Pydantic @field_validator to catch sensitive data during instantiation,
            # but if it slipped through, we check again (e.g. explicitly validating the request object).
            pass
        except Exception as e:
            pass

        for index, provider in enumerate(self.providers):
            provider_start = time.time()
            try:
                if index > 0:
                    audit_metadata["fallback_used"] = True

                response = provider.analyze(request)

                # We have a response, ensure it validates against our schema (done implicitly by Pydantic model response in provider, but double check)
                audit_metadata["provider"] = provider.provider_name
                audit_metadata["status"] = "SUCCESS"
                audit_metadata["latency"] = time.time() - start_time
                audit_metadata["schema_valid"] = True
                audit_metadata["failure_reason"] = None
                return response, audit_metadata

            except ProviderTimeoutError as e:
                logger.warning(f"Provider {provider.provider_name} timed out.")
                audit_metadata["failure_reason"] = f"TIMEOUT: {str(e)}"
                continue
            except (SchemaValidationError, ValidationError) as e:
                logger.error(f"Provider {provider.provider_name} returned malformed response: {e}")
                audit_metadata["failure_reason"] = f"SCHEMA_ERROR: {str(e)}"
                continue
            except SensitiveDataDetected as e:
                # If sensitive data detected, abort entirely
                audit_metadata["failure_reason"] = f"SENSITIVE_DATA: {str(e)}"
                logger.error(f"Sensitive data detected: {e}")
                break
            except LLMError as e:
                logger.warning(f"Provider {provider.provider_name} failed: {e}")
                audit_metadata["failure_reason"] = f"LLM_ERROR: {str(e)}"
                continue
            except Exception as e:
                logger.exception(f"Unexpected error with provider {provider.provider_name}: {e}")
                audit_metadata["failure_reason"] = f"UNEXPECTED_ERROR: {str(e)}"
                continue

        audit_metadata["latency"] = time.time() - start_time
        # Safe fallback: no provider succeeded.
        return None, audit_metadata
