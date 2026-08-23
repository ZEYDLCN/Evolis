"""Minimal auth: password hashing + JWT issuing, both stdlib-only.

Section 32 (Privacy) asks for JWT auth and user data isolation; this is
intentionally minimal (no refresh tokens, no OAuth) — enough to scope every
API call to a single user_id and keep the rest of the codebase honest about
always filtering by it.

JWT (HS256) is hand-rolled rather than pulled in via PyJWT: this app only
ever needs HMAC signing, and PyJWT's default import chain drags in the
`cryptography` package (for algorithms we don't use) which is a common
source of native-extension breakage in minimal environments. Fewer moving
parts for a ~20-line primitive.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import json
import os
import secrets

from apps.api.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, SECRET_KEY

_PBKDF2_ITERATIONS = 200_000


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _PBKDF2_ITERATIONS)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, digest_hex = hashed.split("$")
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _PBKDF2_ITERATIONS)
    return hmac.compare_digest(candidate.hex(), digest_hex)


def _sign(message: bytes) -> str:
    signature = hmac.new(SECRET_KEY.encode(), message, hashlib.sha256).digest()
    return _b64url_encode(signature)


def create_access_token(user_id: str) -> str:
    expire = dt.datetime.utcnow() + dt.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {"sub": user_id, "exp": int(expire.timestamp())}

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signature_b64 = _sign(f"{header_b64}.{payload_b64}".encode())
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str) -> str | None:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        expected_signature = _sign(f"{header_b64}.{payload_b64}".encode())
        if not hmac.compare_digest(expected_signature, signature_b64):
            return None

        payload = json.loads(_b64url_decode(payload_b64))
        if payload.get("exp", 0) < dt.datetime.utcnow().timestamp():
            return None
        return payload.get("sub")
    except (ValueError, KeyError, json.JSONDecodeError):
        return None
