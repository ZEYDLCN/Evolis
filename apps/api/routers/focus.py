from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user
from src.database.base import get_db
from src.database.models import User
from src.services.focus_service import list_focus_sessions, log_focus_session, todays_focus_minutes

router = APIRouter(prefix="/focus-sessions", tags=["focus"])


class LogFocusSessionRequest(BaseModel):
    duration_minutes: int
    project_id: str | None = None
    is_deep_work: bool = True


def _serialize(session) -> dict:
    return {
        "id": session.id,
        "project_id": session.project_id,
        "started_at": session.started_at.isoformat(),
        "duration_minutes": session.duration_minutes,
        "is_deep_work": session.is_deep_work,
    }


@router.post("", status_code=201)
def add_focus_session(
    payload: LogFocusSessionRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    session = log_focus_session(db, user.id, payload.duration_minutes, payload.project_id, payload.is_deep_work)
    return _serialize(session)


@router.get("")
def get_focus_sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    sessions = list_focus_sessions(db, user.id)
    return {
        "sessions": [_serialize(s) for s in sessions],
        "today_minutes": todays_focus_minutes(db, user.id),
    }
