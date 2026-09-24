from __future__ import annotations

import hashlib
import hmac


def expected_signature(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_signature(secret: str, body: bytes, supplied: str | None) -> bool:
    if not secret or not supplied:
        return False
    return hmac.compare_digest(expected_signature(secret, body), supplied)
