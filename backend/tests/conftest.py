import os
import sys

# Runtime now fails closed (unset NETVRIO_ENV == production); the suite runs in test mode
# unless a test explicitly switches to production with monkeypatch.
os.environ.setdefault("NETVRIO_ENV", "test")
# Hundreds of requests come from one TestClient address; individual tests lower this to check 429s.
os.environ.setdefault("NETVRIO_RATE_LIMIT", "100000/minute")

# Ensure backend directory is in python path for all tests
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(BACKEND_DIR, ".."))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
