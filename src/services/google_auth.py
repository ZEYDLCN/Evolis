"""Sign in with Google — verifies a Google Identity Services ID token and
resolves it to a local User, creating one on first sign-in.

Entirely optional: GOOGLE_CLIENT_ID unset means verify_google_credential()
raises GoogleAuthNotConfigured, and the router turns that into an honest
"not available" response rather than a confusing 500 — the same pattern as
ANTHROPIC_API_KEY and NEO4J_URI elsewhere in this codebase. Getting a real
Client ID (console.cloud.google.com/apis/credentials, "OAuth 2.0 Client ID"
of type "Web application") is a one-time setup step for whoever deploys
this, not something this code can supply on its own.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from apps.api.config import GOOGLE_CLIENT_ID
from src.database.models import User


class GoogleAuthNotConfigured(Exception):
    pass


class InvalidGoogleCredential(Exception):
    pass


@dataclass
class GoogleProfile:
    sub: str  # Google's stable per-account identifier — never the email
    email: str
    name: str | None


def verify_google_credential(credential: str) -> GoogleProfile:
    """credential = the ID token a Google Identity Services button hands
    the frontend (the `credential` field of its callback response)."""
    if not GOOGLE_CLIENT_ID:
        raise GoogleAuthNotConfigured

    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token as google_id_token
    except ImportError as exc:
        raise GoogleAuthNotConfigured from exc

    try:
        payload = google_id_token.verify_oauth2_token(credential, google_requests.Request(), GOOGLE_CLIENT_ID)
    except ValueError as exc:  # invalid signature, expired, wrong audience, ...
        raise InvalidGoogleCredential(str(exc)) from exc

    return GoogleProfile(sub=payload["sub"], email=payload["email"], name=payload.get("name"))


def find_or_create_google_user(db: Session, profile: GoogleProfile) -> User:
    user = db.query(User).filter(User.google_sub == profile.sub).first()
    if user:
        return user

    # A password account with this email already exists: link it rather than
    # creating a duplicate. It can still log in with its password too — Google
    # just becomes a second way in.
    user = db.query(User).filter(User.email == profile.email).first()
    if user:
        user.google_sub = profile.sub
        db.commit()
        db.refresh(user)
        return user

    user = User(email=profile.email, google_sub=profile.sub, display_name=profile.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
