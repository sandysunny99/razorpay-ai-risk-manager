"""Single source of truth for runtime mode. Fails closed: an unset NETVRIO_ENV means production,
so a deployment that forgets the variable never trusts the demo tenant header or the dummy
webhook secret."""
import os


def netvrio_env() -> str:
    return os.getenv("NETVRIO_ENV", "production").strip().lower() or "production"


def is_test_env() -> bool:
    return netvrio_env() == "test"


def is_production() -> bool:
    return netvrio_env() == "production"


def demo_mode_enabled() -> bool:
    return not is_production() and os.getenv("NETVRIO_DEMO_MODE", "false").strip().lower() == "true"
