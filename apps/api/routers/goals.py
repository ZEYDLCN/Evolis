import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user, get_lang
from src.database.base import get_db
from src.database.models import User
from src.services.goal_service import complete_goal, create_goal, delete_goal, goals_with_progress, suggest_goals

router = APIRouter(prefix="/goals", tags=["goals"])


class CreateGoalRequest(BaseModel):
    title: str
    description: str | None = None
    metric_key: str | None = None
    target_value: float | None = None
    target_date: dt.date | None = None
    source: str = "manual"


@router.post("", status_code=201)
def add_goal(payload: CreateGoalRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    goal = create_goal(
        db,
        user.id,
        payload.title,
        payload.description,
        payload.metric_key,
        payload.target_value,
        payload.target_date,
        payload.source,
    )
    return {"id": goal.id, "title": goal.title, "status": goal.status}


@router.get("")
def get_goals(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    return goals_with_progress(db, user.id)


@router.get("/suggestions")
def get_goal_suggestions(
    user: User = Depends(get_current_user), db: Session = Depends(get_db), lang: str = Depends(get_lang)
) -> list[dict]:
    return suggest_goals(db, user.id, lang=lang)


@router.post("/{goal_id}/complete")
def mark_goal_complete(goal_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    goal = complete_goal(db, user.id, goal_id)
    if not goal:
        raise HTTPException(404, "Goal not found")
    return {"id": goal.id, "status": goal.status}


@router.delete("/{goal_id}", status_code=204)
def remove_goal(goal_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    if not delete_goal(db, user.id, goal_id):
        raise HTTPException(404, "Goal not found")
