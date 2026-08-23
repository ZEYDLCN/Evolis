import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.base import Base
from src.database.models import User
from src.services.google_auth import (
    GoogleAuthNotConfigured,
    GoogleProfile,
    find_or_create_google_user,
    verify_google_credential,
)


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_verify_raises_when_not_configured(monkeypatch):
    monkeypatch.setattr("src.services.google_auth.GOOGLE_CLIENT_ID", None)
    with pytest.raises(GoogleAuthNotConfigured):
        verify_google_credential("whatever")


def test_creates_new_user_on_first_sign_in():
    db = _make_session()
    profile = GoogleProfile(sub="google-sub-1", email="new@example.com", name="Ada")

    user = find_or_create_google_user(db, profile)

    assert user.email == "new@example.com"
    assert user.google_sub == "google-sub-1"
    assert user.hashed_password is None
    assert user.display_name == "Ada"


def test_repeat_sign_in_returns_same_user():
    db = _make_session()
    profile = GoogleProfile(sub="google-sub-2", email="repeat@example.com", name="Ada")

    first = find_or_create_google_user(db, profile)
    second = find_or_create_google_user(db, profile)

    assert first.id == second.id
    assert db.query(User).count() == 1


def test_links_google_to_existing_password_account_by_email():
    db = _make_session()
    existing = User(email="both@example.com", hashed_password="salt$hash")
    db.add(existing)
    db.commit()

    profile = GoogleProfile(sub="google-sub-3", email="both@example.com", name="Ada")
    linked = find_or_create_google_user(db, profile)

    assert linked.id == existing.id
    assert linked.google_sub == "google-sub-3"
    assert linked.hashed_password == "salt$hash"  # password login still works too
