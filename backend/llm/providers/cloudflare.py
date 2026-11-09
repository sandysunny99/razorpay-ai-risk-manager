import json
import os

import httpx
import pydantic

from backend.llm.errors import ProviderUnavailableError
from backend.llm.health import ProviderHealth, ProviderHealthState
from backend.llm.interfaces import RiskLLMProvider
from backend.llm.schemas import RiskLLMRequest, RiskLLMResponse


class CloudflareProvider(RiskLLMProvider):
    provider_name = "cloudflare"

    def __init__(self, account_id: str = None, token: str = None):
        self.account_id = account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.token = token or os.getenv("CLOUDFLARE_API_TOKEN")
        self.model = os.getenv("CLOUDFLARE_MODEL", "@cf/meta/llama-2-7b-chat-int8")

    def _get_url(self) -> str:
        if not self.account_id:
            raise ProviderUnavailableError("Missing account_id")
        return f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model}"

    def analyze(self, request: RiskLLMRequest, timeout: float = 5.0) -> RiskLLMResponse:
        if not self.token or not self.account_id:
            return RiskLLMResponse(status="MISCONFIGURED", explanation="Credentials missing")

        payload = request.model_dump()
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # Build AI-safe request content
        context_parts = [
            f"Event ID: {payload.get('event_id')}",
            f"Risk Level: {payload.get('risk_level')}, Risk Score: {payload.get('risk_score')}",
            f"Amount: {payload.get('amount')} {payload.get('currency')}",
            f"Features: {json.dumps(payload.get('risk_features', {}))}",
            f"Zombie Signal: {json.dumps(payload.get('zombie_signal', {}))}",
            f"Trusted Evidence IDs: {[payload.get('evidence_package_id')] if payload.get('evidence_package_id') else []}",
            f"Evidence Summaries: {json.dumps(payload.get('evidence_summary', []))}"
        ]
        prompt = "Analyze this transaction.\n" + "\n".join(context_parts)

        data = {
            "messages": [
                {"role": "system", "content": "You are an advisory AI. Output strictly valid JSON with keys: recommended_action, confidence, explanation, cited_evidence_ids. recommended_action MUST be one of: ALLOW, REVIEW, BLOCK, REQUIRE_STEP_UP, QUARANTINE."},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(self._get_url(), headers=headers, json=data)

            if resp.status_code == 429:
                return RiskLLMResponse(status="UNAVAILABLE", explanation="Rate limit exceeded")
            if resp.status_code == 401 or resp.status_code == 403:
                return RiskLLMResponse(status="ERROR", explanation="Authentication failed")
            resp.raise_for_status()

            result = resp.json()
            if "result" not in result or "response" not in result["result"]:
                return RiskLLMResponse(status="INVALID", explanation="Malformed response from provider")

            ai_text = result["result"]["response"]
            # Try to parse AI text as JSON
            ai_data = json.loads(ai_text)

            # The RiskLLMResponse schema will do the strict validation
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
        if not self.token or not self.account_id:
            return ProviderHealth(self.provider_name, ProviderHealthState.NOT_VERIFIED, "Missing credentials")
        return ProviderHealth(self.provider_name, ProviderHealthState.NOT_VERIFIED, "Configured but untested")
