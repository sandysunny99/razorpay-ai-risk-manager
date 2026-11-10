"""Google Gemini via its OpenAI-compatible endpoint."""
from backend.llm.providers.openai_compat import OpenAICompatibleProvider


class GeminiProvider(OpenAICompatibleProvider):
    provider_name = "gemini"
    url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    key_env = ("GEMINI_API_KEY",)
    model_env = "GEMINI_MODEL"
    default_model = "gemini-flash-lite-latest"  # alias tracks the current model, so it does not retire
