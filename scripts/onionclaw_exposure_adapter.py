#!/usr/bin/env python3
"""OnionClaw -> Netvrio card-exposure adapter.

Run this on the isolated collector host that runs OnionClaw (https://github.com/jacobjandon/onionclaw),
never inside the payment API. It reads OnionClaw output (JSON results, Markdown reports or fetched
page text), finds Luhn-valid card numbers, converts each one immediately into the keyed fingerprint
Netvrio already uses (``fp_`` + first 16 hex of HMAC-SHA256(FINGERPRINT_HMAC_SECRET, PAN)), drops the
number, and sends only fingerprints to ``POST /intel/exposures``, signed with EXPOSURE_FEED_SECRET.

Card numbers are never printed, logged, written to disk or transmitted by this script. The host that
handles leaked dumps is still in PCI DSS scope; get legal sign-off before collecting from Tor sources
(OnionClaw's own README: automated access "may be illegal in your country").

Usage:
  python scripts/onionclaw_exposure_adapter.py report.json pages/*.txt            # dry run: counts only
  python scripts/onionclaw_exposure_adapter.py report.json --post https://netvrio.example/intel/exposures
Env: FINGERPRINT_HMAC_SECRET (hex), EXPOSURE_FEED_SECRET (for --post).
"""
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Iterable, Iterator, List, Optional, Tuple
from urllib.parse import urlparse
import urllib.request

CANDIDATE_RE = re.compile(r"(?<![\d])(?:\d[ -]?){12,18}\d(?![\d])")
DIGIT_RUN = re.compile(r"\d{4,}")
MAX_FINDINGS_PER_REQUEST = 1000


def luhn_valid(number: str) -> bool:
    total, parity = 0, len(number) % 2
    for i, ch in enumerate(number):
        d = ord(ch) - 48
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def fingerprint(secret: bytes, pan: str) -> str:
    """Must stay identical to backend/security/card_reference.py (APPROVED_FINGERPRINT mode)."""
    return "fp_" + hmac.new(secret, pan.encode("utf-8"), hashlib.sha256).hexdigest()[:16]


def extract_fingerprints(text: str, secret: bytes) -> Iterator[str]:
    """Yield fingerprints of Luhn-valid 13-19 digit numbers. The PAN never leaves this function."""
    for match in CANDIDATE_RE.finditer(text):
        digits = re.sub(r"[ -]", "", match.group(0))
        if 13 <= len(digits) <= 19 and luhn_valid(digits) and len(set(digits)) > 2:
            yield fingerprint(secret, digits)


def _safe_reference(value: str) -> str:
    """Site label only (host of the source URL), with digit runs removed."""
    host = urlparse(value).hostname if "://" in value else value
    return DIGIT_RUN.sub("#", (host or "unknown"))[:120]


def _texts_from_file(path: Path) -> Iterator[Tuple[str, str]]:
    """Yield (reference, text) pairs. Understands OnionClaw JSON result lists; anything else is text."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    try:
        data = json.loads(raw)
    except ValueError:
        yield _safe_reference(path.name), raw
        return
    items = data if isinstance(data, list) else data.get("results", [data]) if isinstance(data, dict) else []
    for item in items:
        if isinstance(item, dict):
            ref = _safe_reference(str(item.get("url") or item.get("source") or path.name))
            yield ref, json.dumps(item)
        else:
            yield _safe_reference(path.name), str(item)


def collect(paths: Iterable[Path], secret: bytes) -> List[dict]:
    seen = {}
    now = int(time.time())
    for path in paths:
        for reference, text in _texts_from_file(path):
            for fp in extract_fingerprints(text, secret):
                seen.setdefault(fp, {"fingerprint": fp, "reference": reference, "observed_at": now, "confidence": 0.9})
    return list(seen.values())


def post_findings(url: str, findings: List[dict], feed_secret: str, source: str = "onionclaw") -> List[dict]:
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http") or (
        parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1")
    ):
        raise ValueError("refusing to send findings over plain HTTP to a non-local host")
    responses = []
    for i in range(0, len(findings), MAX_FINDINGS_PER_REQUEST):
        body = json.dumps({"source": source, "findings": findings[i:i + MAX_FINDINGS_PER_REQUEST]},
                          separators=(",", ":")).encode()
        ts = str(int(time.time()))
        sig = "sha256=" + hmac.new(feed_secret.encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()
        req = urllib.request.Request(url, data=body, method="POST", headers={  # noqa: S310 — scheme checked above
            "content-type": "application/json", "x-netvrio-timestamp": ts, "x-netvrio-signature": sig,
        })
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 — scheme checked above
            responses.append(json.loads(resp.read()))
    return responses


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--post", metavar="URL", help="Netvrio /intel/exposures endpoint")
    ap.add_argument("--source", default="onionclaw")
    args = ap.parse_args(argv)

    secret_hex = os.getenv("FINGERPRINT_HMAC_SECRET")
    if not secret_hex:
        print("FINGERPRINT_HMAC_SECRET (hex) is required", file=sys.stderr)
        return 2
    findings = collect(args.files, bytes.fromhex(secret_hex))
    print(f"{len(findings)} exposed card fingerprint(s) found")
    for f in findings[:20]:
        print(f"  {f['fingerprint']}  from {f['reference']}")
    if args.post and findings:
        feed_secret = os.getenv("EXPOSURE_FEED_SECRET")
        if not feed_secret:
            print("EXPOSURE_FEED_SECRET is required for --post", file=sys.stderr)
            return 2
        for r in post_findings(args.post, findings, feed_secret, args.source):
            print(f"Netvrio accepted {r['accepted']} (new {r['new']}), tokens revoked: {r['tokens_revoked']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
