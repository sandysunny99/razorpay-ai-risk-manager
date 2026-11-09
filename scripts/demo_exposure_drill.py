#!/usr/bin/env python3
"""Exposure-monitoring drill against a running Netvrio API (demo mode only).

Builds a synthetic "leak dump" containing the synthetic card numbers behind a few of the live
generator's tokens (non-issuable 999990 range), runs the OnionClaw adapter over it, and posts the
fingerprints. Watch Live Operations: the linked tokens are revoked and their next payments block.

Requires the same FINGERPRINT_HMAC_SECRET and EXPOSURE_FEED_SECRET as the API.
"""
import argparse
from pathlib import Path
import random
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import onionclaw_exposure_adapter as adapter  # noqa: E402

from backend.realtime.generator import _ACTIVE_TOKENS, synthetic_pan  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--cards", type=int, default=5)
    args = ap.parse_args()

    tokens = random.sample(_ACTIVE_TOKENS, args.cards)
    lines = [f"[synthetic dump] cc|{synthetic_pan(t)}|12/29|demo" for t in tokens]
    with tempfile.TemporaryDirectory() as tmp:
        dump = Path(tmp) / "synthetic_leak.txt"
        dump.write_text("\n".join(lines), encoding="utf-8")
        return adapter.main([str(dump), "--post", f"{args.api}/intel/exposures", "--source", "drill"])


if __name__ == "__main__":
    sys.exit(main())
