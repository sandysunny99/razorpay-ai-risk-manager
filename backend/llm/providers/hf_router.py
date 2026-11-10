"""Hugging Face Inference Providers via the OpenAI-compatible router.

The older api-inference.huggingface.co endpoint (used by HuggingFaceProvider) has been retired;
this is what the "huggingface" entry in NETVRIO_LLM_CHAIN uses. Accepts HF_API_KEY or HF_TOKEN.
"""
from backend.llm.providers.openai_compat import OpenAICompatibleProvider


class HuggingFaceRouterProvider(OpenAICompatibleProvider):
    provider_name = "huggingface"
    url = "https://router.huggingface.co/v1/chat/completions"
    key_env = ("HF_API_KEY", "HF_TOKEN")
    model_env = "HF_MODEL"
    default_model = "meta-llama/Llama-3.1-8B-Instruct"
    json_mode = False
