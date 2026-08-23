"""Personal Timeline — section 19: topics grouped by month."""
from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user
from src.database.base import get_db
from src.database.models import Entry, EntryTopic, User

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("")
def get_timeline(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    rows = db.execute(
        select(Entry.entry_date, EntryTopic.topic)
        .join(EntryTopic, EntryTopic.entry_id == Entry.id)
        .where(Entry.user_id == user.id)
        .order_by(Entry.entry_date)
    ).all()

    by_month: dict[str, list[str]] = defaultdict(list)
    for entry_date, topic in rows:
        key = entry_date.strftime("%Y-%m")
        if topic not in by_month[key]:
            by_month[key].append(topic)

    return dict(sorted(by_month.items()))
