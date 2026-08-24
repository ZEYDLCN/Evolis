"""Overview dashboard — one aggregate call instead of the frontend firing
~8 separate requests for interests/skills/behavior/streak/versions/etc."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user
from src.analytics.dashboard import build_dashboard_summary
from src.database.base import get_db
from src.database.models import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_dashboard_summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return build_dashboard_summary(db, user.id, display_name=user.display_name).to_dict()
