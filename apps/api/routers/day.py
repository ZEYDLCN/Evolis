import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user
from src.analytics.day_detail import build_day_detail
from src.database.base import get_db
from src.database.models import User

router = APIRouter(prefix="/day", tags=["day"])


@router.get("/{date}")
def get_day_detail(date: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    try:
        day = dt.date.fromisoformat(date)
    except ValueError:
        raise HTTPException(422, "date must be YYYY-MM-DD")
    return build_day_detail(db, user.id, day)
