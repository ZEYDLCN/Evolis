import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user
from src.analytics.turning_points import detect_turning_point_candidates
from src.database.base import get_db
from src.database.models import User
from src.services.evolution_event_service import (
    create_event,
    decision_impact,
    delete_event,
    get_event,
    list_events,
    rank_decisions_by_impact,
    serialize_event,
)

router = APIRouter(prefix="/evolution-events", tags=["evolution-events"])


class CreateEventRequest(BaseModel):
    type: str  # decision | turning_point | milestone
    title: str
    event_date: dt.date
    description: str | None = None
    alternatives: list[str] | None = None
    chosen: str | None = None


@router.post("", status_code=201)
def add_event(
    payload: CreateEventRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    if payload.type not in {"decision", "turning_point", "milestone"}:
        raise HTTPException(422, "type must be decision, turning_point, or milestone")

    metadata = None
    if payload.alternatives or payload.chosen:
        metadata = {"alternatives": payload.alternatives or [], "chosen": payload.chosen}

    event = create_event(
        db,
        user.id,
        payload.type,
        payload.title,
        payload.event_date,
        description=payload.description,
        source="manual",
        metadata=metadata,
    )
    return serialize_event(event)


@router.get("")
def get_events(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    return [serialize_event(e) for e in list_events(db, user.id)]


@router.get("/turning-points/candidates")
def get_turning_point_candidates(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    existing = {
        e.event_date.date() if isinstance(e.event_date, dt.datetime) else e.event_date
        for e in list_events(db, user.id)
        if e.type == "turning_point"
    }
    candidates = detect_turning_point_candidates(db, user.id, existing_dates=existing)
    return [c.to_dict() for c in candidates]


@router.get("/decisions/ranked")
def get_ranked_decisions(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    return rank_decisions_by_impact(db, user.id)


@router.get("/{event_id}/impact")
def get_event_impact(event_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    event = get_event(db, user.id, event_id)
    if not event:
        raise HTTPException(404, "Event not found")
    return decision_impact(db, user.id, event)


@router.delete("/{event_id}", status_code=204)
def remove_event(event_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    if not delete_event(db, user.id, event_id):
        raise HTTPException(404, "Event not found")
