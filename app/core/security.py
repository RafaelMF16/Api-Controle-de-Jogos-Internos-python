from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta

import jwt


def hash_password(password: str, iterations: int = 100_000) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return "pbkdf2_sha256${iterations}${salt}${digest}".format(
        iterations=iterations,
        salt=base64.b64encode(salt).decode("utf-8"),
        digest=base64.b64encode(digest).decode("utf-8"),
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        _, iterations_raw, salt_raw, digest_raw = stored_hash.split("$", maxsplit=3)
    except ValueError:
        return False

    salt = base64.b64decode(salt_raw.encode("utf-8"))
    expected_digest = base64.b64decode(digest_raw.encode("utf-8"))
    candidate_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        int(iterations_raw),
    )
    return hmac.compare_digest(candidate_digest, expected_digest)


def create_access_token(
    data: dict[str, str | int | None],
    secret_key: str,
    algorithm: str,
    expires_minutes: int,
) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_access_token(token: str, secret_key: str, algorithm: str) -> dict[str, str | int | None]:
    return jwt.decode(token, secret_key, algorithms=[algorithm])
