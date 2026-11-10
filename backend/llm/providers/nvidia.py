"""NVIDIA NIM (build.nvidia.com) via its OpenAI-compatible endpoint."""
from backend.llm.providers.openai_compat import OpenAICompatibleProvider


class NvidiaProvider(OpenAICompatibleProvider):
    provider_name = "nvidia"
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    key_env = ("NVIDIA_API_KEY",)
    model_env = "NVIDIA_MODEL"
    default_model = "openai/gpt-oss-20b"
    json_mode = False  # not every NIM model accepts response_format; the prompt demands JSON instead
