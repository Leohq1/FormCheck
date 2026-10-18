import hashlib
import hmac
import secrets

from formcheck.config import get_settings


def generate_capability_token() -> str:
    return secrets.token_urlsafe(32)


def hash_capability_token(token: str) -> str:
    pepper = get_settings().capability_token_pepper.encode("utf-8")
    return hashlib.sha256(pepper + token.encode("utf-8")).hexdigest()


def tokens_match(provided: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_capability_token(provided), stored_hash)
