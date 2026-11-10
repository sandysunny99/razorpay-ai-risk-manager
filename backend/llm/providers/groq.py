"""Groq (https://console.groq.com) via its OpenAI-compatible endpoint. Not to be confused with xAI Grok."""
from backend.llm.providers.openai_compat import OpenAICompatibleProvider


class GroqProvider(OpenAICompatibleProvider):
    provider_name = "groq"
    url = "https://api.groq.com/openai/v1/chat/completions"
    key_env = ("GROQ_API_KEY",)
    model_env = "GROQ_MODEL"
    default_model = "openai/gpt-oss-20b"
