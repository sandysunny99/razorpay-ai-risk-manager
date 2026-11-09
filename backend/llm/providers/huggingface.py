import json
import os

import httpx
import pydantic

from backend.llm.health import ProviderHealth, ProviderHealthState
from backend.llm.interfaces import RiskLLMProvider
from backend.llm.schemas import RiskLLMRequest, RiskLLMResponse


class HuggingFaceProvider(RiskLLMProvider):
    provider_name = "huggingface"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("HF_API_KEY")
        self.model = os.getenv("HF_MODEL", "meta-llama/Llama-2-7b-chat-hf")

    def _get_url(self) -> str:
        return f"https://api-inference.huggingface.co/models/{self.model}"

    def analyze(self, request: RiskLLMRequest, timeout: float = 5.0) -> RiskLLMResponse:
        if not self.api_key:
            return RiskLLMResponse(status="MISCONFIGURED", explanation="Credentials missing")

        payload = request.model_dump()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        context_parts = [
            f"Event ID: {payload.get('event_id')}",
            f"Risk Level: {payload.get('risk_level')}, Risk Score: {payload.get('risk_score')}",
            f"Amount: {payload.get('amount')} {payload.get('currency')}",
            f"Features: {json.dumps(payload.get('risk_features', {}))}",
            f"Zombie Signal: {json.dumps(payload.get('zombie_signal', {}))}",
            f"Trusted Evidence IDs: {[payload.get('evidence_package_id')] if payload.get('evidence_package_id') else []}",
            f"Evidence Summaries: {json.dumps(payload.get('evidence_summary', []))}"
        ]

        system_prompt = "You are an advisory AI. Output strictly valid JSON with keys: recommended_action, confidence, explanation, cited_evidence_ids. recommended_action MUST be one of: ALLOW, REVIEW, BLOCK, REQUIRE_STEP_UP, QUARANTINE.\n"
        prompt = system_prompt + "Analyze this transaction.\n" + "\n".join(context_parts)

        data = {
            "inputs": prompt,
            "parameters": {"return_full_text": False, "max_new_tokens": 150}
        }

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(self._get_url(), headers=headers, json=data)

            if resp.status_code == 429:
                return RiskLLMResponse(status="UNAVAILABLE", explanation="Rate limit exceeded")
            if resp.status_code == 401 or resp.status_code == 403:
                return RiskLLMResponse(status="ERROR", explanation="Authentication failed")
            # HF API often returns 503 while loading model
            if resp.status_code == 503:
                return RiskLLMResponse(status="UNAVAILABLE", explanation="Model loading")
            resp.raise_for_status()

            result = resp.json()
            if not isinstance(result, list) or len(result) == 0 or "generated_text" not in result[0]:
                return RiskLLMResponse(status="INVALID", explanation="Malformed response from provider")

            ai_text = result[0]["generated_text"]
            # Clean up potential markdown formatting
            ai_text = ai_text.strip().removeprefix("```json").removesuffix("```").strip()
            ai_data = json.loads(ai_text)

            return RiskLLMResponse(
                status="SUCCESS",
                recommended_action=ai_data.get("recommended_action"),
                confidence=ai_data.get("confidence"),
                explanation=ai_data.get("explanation"),
                cited_evidence_ids=ai_data.get("cited_evidence_ids", []),
                provider=self.provider_name,
                model=self.model
            )

        except httpx.TimeoutException:
            return RiskLLMResponse(status="TIMEOUT", explanation="Provider timed out")
        except httpx.RequestError:
            return RiskLLMResponse(status="UNAVAILABLE", explanation="Connection error to provider")
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500:
                return RiskLLMResponse(status="ERROR", explanation="Provider internal error")
            return RiskLLMResponse(status="ERROR", explanation="Unexpected HTTP error")
        except json.JSONDecodeError:
            return RiskLLMResponse(status="INVALID", explanation="Failed to parse AI output as JSON")
        except pydantic.ValidationError:
            return RiskLLMResponse(status="INVALID", explanation="AI output failed schema validation")
        except Exception:
            return RiskLLMResponse(status="ERROR", explanation="Unexpected internal error")

    def health(self) -> ProviderHealth:
        if not self.api_key:
            return ProviderHealth(self.provider_name, ProviderHealthState.NOT_VERIFIED, "Missing credentials")
        return ProviderHealth(self.provider_name, ProviderHealthState.NOT_VERIFIED, "Configured but untested")



