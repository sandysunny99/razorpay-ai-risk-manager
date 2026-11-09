"""PII masking for free text, using Presidio (https://github.com/data-privacy-stack/presidio, MIT).

Applied to customer-supplied free text (payment notes, user input) before it reaches evidence,
the audit trail, the live stream or any LLM. Engine selection (NETVRIO_PII_ENGINE):

  auto (default)  Presidio when presidio-analyzer and the spaCy model are installed, else regex
  presidio        Presidio required; falls back to regex with a logged warning if unavailable
  regex           built-in patterns only (no NLP, so person names are not detected)

Both engines cover cards (Luhn-checked), e-mail, UPI IDs, Indian mobile numbers, Aadhaar, PAN
(the Indian tax id) and IP addresses, and replace each finding with <ENTITY_TYPE>.
"""
import logging
import os
import re
import threading
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

ENTITIES = ["CREDIT_CARD", "EMAIL_ADDRESS", "UPI_ID", "IN_MOBILE", "IN_AADHAAR", "IN_PAN", "IP_ADDRESS", "PERSON"]

# Order matters for the regex engine: e-mail before UPI (both contain "@").
_REGEX = [
    ("EMAIL_ADDRESS", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    # A UPI handle has no dot-domain after it; a trailing full stop (end of sentence) is fine.
    ("UPI_ID", re.compile(r"\b[\w.\-]{2,256}@[a-zA-Z][a-zA-Z0-9]{1,63}\b(?!\.[a-zA-Z])")),
    ("CREDIT_CARD", re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")),
    ("IN_AADHAAR", re.compile(r"(?<!\d)[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}(?!\d)")),
    ("IN_MOBILE", re.compile(r"(?<![\w+])(?:\+91[ -]?|0)?[6-9]\d{9}(?!\d)")),
    ("IN_PAN", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")),
    ("IP_ADDRESS", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
]


def _luhn(digits: str) -> bool:
    total, parity = 0, len(digits) % 2
    for i, ch in enumerate(digits):
        d = int(ch)
        if i % 2 == parity:
            d = d * 2 - 9 if d * 2 > 9 else d * 2
        total += d
    return total % 10 == 0


def _regex_scrub(text: str) -> Tuple[str, List[str]]:
    found: List[str] = []
    for entity, pattern in _REGEX:
        def repl(m, entity=entity):
            if entity == "CREDIT_CARD":
                digits = re.sub(r"[ -]", "", m.group(0))
                if not (13 <= len(digits) <= 19 and _luhn(digits)):
                    return m.group(0)
            found.append(entity)
            return f"<{entity}>"
        text = pattern.sub(repl, text)
    return text, found


class PiiScrubber:
    def __init__(self):
        self._lock = threading.Lock()
        self._initialised = False
        self._analyzer = None
        self._anonymizer = None
        self.engine = "regex"
        self.error: Optional[str] = None

    def _init(self) -> None:
        with self._lock:
            if self._initialised:
                return
            self._initialised = True
            mode = os.getenv("NETVRIO_PII_ENGINE", "auto").lower()
            if mode == "regex":
                return
            try:
                from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
                from presidio_analyzer.nlp_engine import NlpEngineProvider
                from presidio_analyzer.predefined_recognizers import InAadhaarRecognizer, InPanRecognizer
                from presidio_anonymizer import AnonymizerEngine

                nlp = NlpEngineProvider(nlp_configuration={
                    "nlp_engine_name": "spacy",
                    "models": [{"lang_code": "en", "model_name": os.getenv("NETVRIO_PII_SPACY_MODEL", "en_core_web_sm")}],
                }).create_engine()
                registry = RecognizerRegistry()
                registry.load_predefined_recognizers(languages=["en"])
                registry.add_recognizer(InAadhaarRecognizer())
                registry.add_recognizer(InPanRecognizer())
                registry.add_recognizer(PatternRecognizer(
                    supported_entity="UPI_ID",
                    patterns=[Pattern("upi_vpa", r"\b[\w.\-]{2,256}@[a-zA-Z][a-zA-Z0-9]{1,63}\b(?!\.[a-zA-Z])", 0.6)],
                    context=["upi", "vpa", "pay", "gpay", "phonepe", "paytm"],
                ))
                registry.add_recognizer(PatternRecognizer(
                    supported_entity="IN_MOBILE",
                    patterns=[Pattern("in_mobile", r"(?<![\w+])(?:\+91[ -]?|0)?[6-9]\d{9}(?!\d)", 0.6)],
                    context=["phone", "mobile", "call", "whatsapp", "contact"],
                ))
                self._analyzer = AnalyzerEngine(registry=registry, nlp_engine=nlp, supported_languages=["en"])
                self._anonymizer = AnonymizerEngine()
                self.engine = "presidio"
            except Exception as exc:  # noqa: BLE001 — missing package or model: degrade, never fail
                self.error = type(exc).__name__
                self.engine = "regex"
                log = logger.warning if mode == "presidio" else logger.info
                log("Presidio unavailable (%s); using regex PII masking", self.error)

    def scrub(self, text: str) -> Tuple[str, List[str]]:
        """Return (masked_text, entity_types_found). Never raises; never returns the input on failure."""
        if not isinstance(text, str) or not text:
            return text, []
        self._init()
        if self._analyzer is not None:
            try:
                from presidio_anonymizer.entities import OperatorConfig

                results = self._analyzer.analyze(text=text, language="en", entities=ENTITIES, score_threshold=0.4)
                if not results:
                    # Presidio's built-in card/phone rules are strict; run the patterns as a safety net.
                    return _regex_scrub(text)
                masked = self._anonymizer.anonymize(
                    text=text, analyzer_results=results,
                    operators={"DEFAULT": OperatorConfig("replace", {"new_value": "<PII>"}),
                               **{e: OperatorConfig("replace", {"new_value": f"<{e}>"}) for e in ENTITIES}},
                ).text
                # Second pass catches anything Presidio scored below threshold (e.g. bare UPI IDs).
                masked, extra = _regex_scrub(masked)
                return masked, sorted({r.entity_type for r in results} | set(extra))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Presidio scrub failed (%s); using regex", type(exc).__name__)
        return _regex_scrub(text)

    def status(self) -> dict:
        self._init()
        return {"engine": self.engine, "error": self.error, "entities": ENTITIES if self.engine == "presidio" else [e for e, _ in _REGEX]}


pii_scrubber = PiiScrubber()

FREE_TEXT_FIELDS = ("note", "notes", "user_input", "description", "remarks")
