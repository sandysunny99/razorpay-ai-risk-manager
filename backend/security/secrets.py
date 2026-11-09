import os
from typing import Optional


class SecretString(str):
    """
    A string subclass that prevents accidental logging of secrets.
    """
    def __repr__(self) -> str:
        return "SecretString('**********')"

    def __str__(self) -> str:
        return "**********"

def get_secret(key: str) -> Optional[SecretString]:
    """
    Loads a secret from the environment, returning it as a SecretString.
    """
    val = os.environ.get(key)
    if val is not None:
        return SecretString(val)
    return None
