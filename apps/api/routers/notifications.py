from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user, get_lang
from src.database.base import get_db
from src.database.models import User
from src.services.notification_service import build_notifications

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def get_notifications(
    user: User = Depends(get_current_user), db: Session = Depends(get_db), lang: str = Depends(get_lang)
) -> list[dict]:
    return build_notifications(db, user.id, lang=lang)
