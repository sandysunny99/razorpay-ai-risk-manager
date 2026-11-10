"""Shared adapter for providers that speak the OpenAI chat-completions protocol (Groq, Gemini's
OpenAI endpoint, NVIDIA NIM). Each concrete provider only sets its endpoint, key variables and
default model. Endpoints are fixed in code (never taken from a request), keys come from the
environment, and the prompt carries only the masked, minimal context in RiskLLMRequest.
"""
import json
import os
from typing import Optional, Sequence

import httpx
import pydantic

from backend.llm.health import ProviderHealth, ProviderHealthState
from backend.llm.interfaces import RiskLLMProvider
from backend.llm.schemas import RiskLLMRequest, RiskLLMResponse

SYSTEM_PROMPT = (
    "You are an advisory AI for a payment-risk analyst. You never make the decision; a deterministic policy "
    "engine does. Output strictly valid JSON with keys: recommended_action, confidence, explanation, "
    "cited_evidence_ids. recommended_action MUST be one of: ALLOW, REVIEW, BLOCK, REQUIRE_STEP_UP, QUARANTINE. "
    "confidence is an integer 0-100. Only cite evidence IDs that appear in the input."
)


def build_prompt(request: RiskLLMRequest) -> str:
    p = request.model_dump()
    parts = [
        f"Event ID: {p.get('event_id')}",
        f"Risk Level: {p.get('risk_level')}, Risk Score: {p.get('risk_score')}",
        f"Amount: {p.get('amount')} {p.get('currency')}",
        f"Features: {json.dumps(p.get('risk_features', {}))}",
        f"Zombie Signal: {json.dumps(p.get('zombie_signal', {}))}",
        f"Trusted Evidence IDs: {[p.get('evidence_package_id')] if p.get('evidence_package_id') else []}",
        f"Evidence Summaries: {json.dumps(p.get('evidence_summary', []))}",
    ]
    return "Analyze this transaction.\n" + "\n".join(parts)


def normalize_confidence(value):
    """Models sometimes answer 0.8 instead of 80. Convert a 0-1 decimal to a percentage; leave
    anything else for strict schema validation to accept or reject."""
    if isinstance(value, float) and 0.0 <= value <= 1.0:
        return int(round(value * 100))
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def parse_json_object(content) -> dict:
    """Accept a dict, a JSON string, a fenced block, or JSON embedded in prose; raise ValueError otherwise."""
    if isinstance(content, dict):
        return content
    text = _strip_fences(str(content))
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise
        data = json.loads(text[start:end + 1])
    if not isinstance(data, dict):
        raise json.JSONDecodeError("expected an object", text, 0)
    return data


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    return text.strip()


class OpenAICompatibleProvider(RiskLLMProvider):
    provider_name = "openai_compatible"
    url: str = ""
    key_env: Sequence[str] = ()
    model_env: str = ""
    default_model: str = ""
    json_mode: bool = True

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or next((os.getenv(k) for k in self.key_env if os.getenv(k)), None)
        self.model = model or os.getenv(self.model_env) or self.default_model

    def _body(self, request: RiskLLMRequest) -> dict:
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": build_prompt(request)}],
            "temperature": 0,
            # Reasoning models (gpt-oss) spend tokens before the answer, so leave headroom.
            "max_tokens": 1024,
        }
        if self.json_mode:
            body["response_format"] = {"type": "json_object"}
        return body

    def analyze(self, request: RiskLLMRequest, timeout: float = 8.0) -> RiskLLMResponse:
        if not self.api_key:
            return RiskLLMResponse(status="MISCONFIGURED", explanation="Credentials missing")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(self.url, headers=headers, json=self._body(request))
            if resp.status_code == 429:
                return RiskLLMResponse(status="UNAVAILABLE", explanation="Rate limit exceeded")
            if resp.status_code in (401, 403):
                return RiskLLMResponse(status="ERROR", explanation="Authentication failed")
            if resp.status_code in (404, 410):
                # Retired or unknown model: a configuration problem, reported clearly so it is fixed.
                return RiskLLMResponse(status="MISCONFIGURED", explanation=f"Model {self.model} unavailable (HTTP {resp.status_code})")
            resp.raise_for_status()
            result = resp.json()
            if not isinstance(result, dict) or not result.get("choices"):
                return RiskLLMResponse(status="INVALID", explanation="Malformed response from provider")
            ai_data = parse_json_object(result["choices"][0]["message"]["content"])
            return RiskLLMResponse(
                status="SUCCESS",
                recommended_action=ai_data.get("recommended_action"),
                confidence=normalize_confidence(ai_data.get("confidence")),
                explanation=ai_data.get("explanation"),
                cited_evidence_ids=ai_data.get("cited_evidence_ids", []),
                provider=self.provider_name,
                model=self.model,
            )
        except httpx.TimeoutException:
            return RiskLLMResponse(status="TIMEOUT", explanation="Provider timed out")
        except httpx.RequestError:
            return RiskLLMResponse(status="UNAVAILABLE", explanation="Connection error to provider")
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500:
                return RiskLLMResponse(status="ERROR", explanation="Provider internal error")
            return RiskLLMResponse(status="ERROR", explanation=f"HTTP {e.response.status_code} from provider")
        except (json.JSONDecodeError, KeyError, IndexError, TypeError, AttributeError):
            return RiskLLMResponse(status="INVALID", explanation="Failed to parse AI output as JSON")
        except pydantic.ValidationError:
            return RiskLLMResponse(status="INVALID", explanation="AI output failed schema validation")
        except Exception:
            return RiskLLMResponse(status="ERROR", explanation="Unexpected internal error")

    def health(self) -> ProviderHealth:
        if not self.api_key:
            return ProviderHealth(self.provider_name, ProviderHealthState.NOT_VERIFIED, "Missing credentials")
        return ProviderHealth(self.provider_name, ProviderHealthState.NOT_VERIFIED, "Configured but untested")
