import logging
from typing import List, Optional

from .schemas import RiskLLMResponse

logger = logging.getLogger(__name__)

def validate_llm_advisory(advisory: Optional[RiskLLMResponse], valid_evidence_ids: List[str]) -> Optional[RiskLLMResponse]:
    if not advisory:
        return None

    # Check for evidence fabrication
    for cited_id in advisory.cited_evidence_ids:
        if cited_id not in valid_evidence_ids:
            logger.warning(f"LLM cited unknown evidence ID: {cited_id}. Rejecting advisory.")
            return None # Reject advisory entirely

    # Check for malicious prompt injection behavior in explanation
    # (If prompt injection caused the LLM to output system overrides in its explanation)
    lower_exp = advisory.explanation.lower()
    if "ignore previous instructions" in lower_exp or "system override" in lower_exp:
        logger.warning("Potential prompt injection detected in LLM output. Rejecting advisory.")
        return None

    return advisory
