import pytest
from cryptography.fernet import Fernet

from src.database.encryption import decrypt_text, encrypt_text, encryption_enabled


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    assert encryption_enabled() is False
    assert encrypt_text("hello") == "hello"
    assert decrypt_text("hello") == "hello"


def test_round_trip_when_enabled(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    assert encryption_enabled() is True

    ciphertext = encrypt_text("Bugün RAG üzerine çalıştım.")
    assert ciphertext != "Bugün RAG üzerine çalıştım."
    assert decrypt_text(ciphertext) == "Bugün RAG üzerine çalıştım."


def test_decrypt_fails_soft_on_wrong_key(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    ciphertext = encrypt_text("secret")

    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    # Wrong key: returns the (still-ciphertext) value rather than raising.
    assert decrypt_text(ciphertext) == ciphertext
