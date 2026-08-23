import datetime as dt

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user
from src.database.base import get_db
from src.database.models import User
from src.services.entry_service import create_entry

router = APIRouter(prefix="/entries", tags=["entries"])


class CreateEntryRequest(BaseModel):
    text: str
    entry_date: dt.date | None = None


class EntryResponse(BaseModel):
    id: str
    raw_text: str
    entry_date: dt.datetime
    completion_status: str | None
    blockers: list[str] | None
    extraction: dict | None

    model_config = ConfigDict(from_attributes=True)


@router.post("", response_model=EntryResponse, status_code=201)
def add_entry(payload: CreateEntryRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> EntryResponse:
    entry = create_entry(db, user.id, payload.text, payload.entry_date)
    return EntryResponse(
        id=entry.id,
        raw_text=entry.raw_text,
        entry_date=entry.entry_date,
        completion_status=entry.completion_status,
        blockers=entry.blockers,
        extraction=entry.extraction_raw,
    )


@router.get("", response_model=list[EntryResponse])
def list_entries(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[EntryResponse]:
    entries = user.entries
    return [
        EntryResponse(
            id=e.id,
            raw_text=e.raw_text,
            entry_date=e.entry_date,
            completion_status=e.completion_status,
            blockers=e.blockers,
            extraction=e.extraction_raw,
        )
        for e in sorted(entries, key=lambda e: e.entry_date, reverse=True)
    ]
