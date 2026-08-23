"""Application-level field encryption — section 32 (Privacy: Encrypted Storage).

Opt-in via ENCRYPTION_KEY: unset, everything behaves exactly as before
(plaintext, `ilike`/`LIKE` queries work normally) — this is the default so
existing deployments and every test in this repo are unaffected. Set it to
a Fernet key (`Fernet.generate_key()`) and `Entry.raw_text` — the one
genuinely sensitive free-text field, a personal daily journal — is
encrypted at rest with AES via `cryptography.fernet`.

Trade-off worth being explicit about: encrypting a column means the
database can no longer do `LIKE` search over it. src/rag/retriever.py's
keyword_search() branches on whether encryption is enabled and, if so,
filters in Python after decrypting the user's own rows instead of pushing
the pattern match into SQL. That's fine at personal-analytics scale (one
user's few thousand entries); it would need a proper searchable-encryption
or client-side-index strategy well before it became a bottleneck.
"""
from __future__ import annotations

import os

from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator


def encryption_enabled() -> bool:
    return bool(os.getenv("ENCRYPTION_KEY"))


def _fernet():
    from cryptography.fernet import Fernet

    key = os.environ["ENCRYPTION_KEY"]
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_text(plaintext: str) -> str:
    if not encryption_enabled():
        return plaintext
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_text(value: str) -> str:
    if not encryption_enabled():
        return value
    from cryptography.fernet import InvalidToken

    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        # Most likely: this row was written before ENCRYPTION_KEY was set
        # (or with a different key). Fail soft rather than 500 the request —
        # the raw stored value is still shown, just not decrypted.
        return value


class EncryptedText(TypeDecorator):
    """A String column that's transparently encrypted/decrypted at the ORM
    boundary. Application code reads/writes plain Python strings; only what
    hits the database differs based on ENCRYPTION_KEY.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return encrypt_text(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return decrypt_text(value)
