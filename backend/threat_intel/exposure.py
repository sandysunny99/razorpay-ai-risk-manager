"""Card exposure monitoring.

Findings arrive from an isolated collector (for example OnionClaw output processed by
scripts/onionclaw_exposure_adapter.py). The collector turns every leaked card number into the
same keyed fingerprint merchants already use (``fp_`` + HMAC-SHA256 with FINGERPRINT_HMAC_SECRET,
see backend/security/card_reference.py) and discards the number. This module therefore never
sees a PAN: it stores fingerprints only.

Matching works two ways:
  * proactive: when a fingerprint is reported exposed, every token the pipeline has seen linked to
    it (per tenant) is revoked at once, so the next use is blocked;
  * inline: a payment that presents an exposed fingerprint, or a token linked to one, is treated as
    a trusted compromise signal by Zombie Card Saver (REVOKE_TOKEN, policy BLOCK).
"""
from collections import defaultdict, deque
from dataclasses import dataclass
import re
import threading
import time
from typing import Deque, Dict, List, Optional, Set, Tuple

FINGERPRINT_RE = re.compile(r"^fp_[0-9a-f]{16}$")
MAX_LINKS = 500_000


@dataclass(frozen=True)
class Exposure:
    fingerprint: str
    source: str
    reference: str
    observed_at: int
    confidence: float
    reported_at: int


class ExposureStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._exposed: Dict[str, Exposure] = {}
        self._fp_tokens: Dict[Tuple[str, str], Set[str]] = defaultdict(set)   # (tenant, fp) -> tokens
        self._token_fp: Dict[Tuple[str, str], str] = {}                        # (tenant, token) -> fp
        self._log: Deque[dict] = deque(maxlen=200)
        self.revoked_via_exposure = 0

    def link(self, tenant_id: str, token: Optional[str], fingerprint: Optional[str]) -> None:
        """Remember token <-> fingerprint pairs observed on accepted traffic."""
        if not token or not fingerprint or not FINGERPRINT_RE.match(fingerprint):
            return
        with self._lock:
            if len(self._token_fp) > MAX_LINKS:
                self._token_fp.clear()
                self._fp_tokens.clear()
            self._token_fp[(tenant_id, token)] = fingerprint
            self._fp_tokens[(tenant_id, fingerprint)].add(token)

    def is_exposed(self, tenant_id: str, token: Optional[str], fingerprint: Optional[str]) -> Optional[Exposure]:
        with self._lock:
            fp = fingerprint if fingerprint and FINGERPRINT_RE.match(fingerprint) else None
            if fp is None and token:
                fp = self._token_fp.get((tenant_id, token))
            return self._exposed.get(fp) if fp else None

    def report(self, findings: List[dict], source: str) -> Tuple[int, Dict[str, List[str]]]:
        """Record findings. Returns (new_count, {tenant: [tokens to revoke]})."""
        now = int(time.time())
        new = 0
        to_revoke: Dict[str, List[str]] = defaultdict(list)
        with self._lock:
            for f in findings:
                fp = f["fingerprint"]
                if fp not in self._exposed:
                    new += 1
                self._exposed[fp] = Exposure(fp, source, f.get("reference", ""), int(f.get("observed_at") or now),
                                             float(f.get("confidence", 0.9)), now)
                for (tenant, linked_fp), tokens in self._fp_tokens.items():
                    if linked_fp == fp:
                        to_revoke[tenant].extend(sorted(tokens))
            self._log.append({"source": source, "reported_at": now, "findings": len(findings), "new": new,
                              "tokens_revoked": sum(len(v) for v in to_revoke.values())})
            self.revoked_via_exposure += sum(len(v) for v in to_revoke.values())
        return new, dict(to_revoke)

    def summary(self) -> dict:
        with self._lock:
            recent = sorted(self._exposed.values(), key=lambda e: e.reported_at, reverse=True)[:20]
            return {
                "exposed_fingerprints": len(self._exposed),
                "tokens_revoked_via_exposure": self.revoked_via_exposure,
                "reports": list(self._log)[::-1][:20],
                "recent": [
                    {"fingerprint": e.fingerprint[:7] + "…", "source": e.source, "reference": e.reference,
                     "observed_at": e.observed_at, "confidence": e.confidence}
                    for e in recent
                ],
            }


exposure_store = ExposureStore()
