import datetime as dt

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user
from src.database.base import get_db
from src.database.models import User
from src.services.search_service import search_all

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(
    q: str = "",
    days: int | None = None,
    topic: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    start = dt.datetime.utcnow() - dt.timedelta(days=days) if days else None
    return search_all(db, user.id, q, start=start, topic=topic)
