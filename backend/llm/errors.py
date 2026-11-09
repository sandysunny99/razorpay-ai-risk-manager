class LLMError(Exception):
    pass

class ProviderTimeoutError(LLMError):
    pass

class ProviderUnavailableError(LLMError):
    pass

class ProviderRateLimitError(LLMError):
    pass

class SchemaValidationError(LLMError):
    pass

class EvidenceValidationError(LLMError):
    pass

class PromptInjectionDetected(LLMError):
    pass

class SensitiveDataDetected(LLMError):
    pass
