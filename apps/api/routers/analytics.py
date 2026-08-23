import datetime as dt

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user
from src.analytics.interests import topic_interest_scores
from src.analytics.productivity import behavior_summary
from src.analytics.skills import skill_scores
from src.database.base import get_db
from src.database.models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _default_range(months: int) -> tuple[dt.datetime, dt.datetime]:
    end = dt.datetime.utcnow()
    start = end - dt.timedelta(days=30 * months)
    return start, end


@router.get("/interests")
def get_interests(months: int = Query(3, ge=1, le=36), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    start, end = _default_range(months)
    return topic_interest_scores(db, user.id, start, end)


@router.get("/skills")
def get_skills(months: int = Query(3, ge=1, le=36), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    start, end = _default_range(months)
    return skill_scores(db, user.id, start, end)


@router.get("/behavior")
def get_behavior(months: int = Query(3, ge=1, le=36), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    start, end = _default_range(months)
    return behavior_summary(db, user.id, start, end)
