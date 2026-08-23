from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from src.database.base import get_db
from src.database.models import User
from src.services.auth_service import create_access_token, hash_password, verify_password
from src.services.google_auth import (
    GoogleAuthNotConfigured,
    InvalidGoogleCredential,
    find_or_create_google_user,
    verify_google_credential,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GoogleLoginRequest(BaseModel):
    credential: str  # the ID token from Google Identity Services' callback response


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(email=payload.email, hashed_password=hash_password(payload.password), display_name=payload.display_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/google/config")
def google_config() -> dict:
    """Lets the frontend decide whether to render the Google button at all,
    without duplicating GOOGLE_CLIENT_ID into a second env var by hand."""
    from apps.api.config import GOOGLE_CLIENT_ID

    return {"enabled": bool(GOOGLE_CLIENT_ID), "client_id": GOOGLE_CLIENT_ID}


@router.post("/google", response_model=TokenResponse)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        profile = verify_google_credential(payload.credential)
    except GoogleAuthNotConfigured:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Google sign-in is not configured on this server")
    except InvalidGoogleCredential:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Google credential")

    user = find_or_create_google_user(db, profile)
    return TokenResponse(access_token=create_access_token(user.id))
