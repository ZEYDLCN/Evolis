"""Privacy — section 32: GDPR-style self-service export and deletion."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user
from src.database.base import get_db
from src.database.models import User
from src.services.account_service import delete_user_account, export_user_data

router = APIRouter(prefix="/me", tags=["account"])


@router.get("")
def get_me(user: User = Depends(get_current_user)) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "google_linked": user.google_sub is not None,
        "created_at": user.created_at.isoformat(),
    }


@router.get("/export")
def export_my_data(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return export_user_data(db, user.id)


@router.delete("", status_code=204)
def delete_my_account(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    delete_user_account(db, user.id)
