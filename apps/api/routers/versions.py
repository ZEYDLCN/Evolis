import datetime as dt

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user
from src.database.base import get_db
from src.database.models import User, Version
from src.versions.snapshot import generate_version, version_metrics_dict

router = APIRouter(prefix="/versions", tags=["versions"])


class GenerateVersionRequest(BaseModel):
    period_start: dt.date
    period_end: dt.date
    label: str | None = None


@router.post("/generate", status_code=201)
def generate(payload: GenerateVersionRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    version = generate_version(
        db,
        user.id,
        dt.datetime.combine(payload.period_start, dt.time.min),
        dt.datetime.combine(payload.period_end, dt.time.min),
        payload.label,
    )
    return {"id": version.id, "label": version.label, "metrics": version_metrics_dict(version)}


@router.get("")
def list_versions(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    versions = db.query(Version).filter(Version.user_id == user.id).order_by(Version.period_start).all()
    return [
        {
            "id": v.id,
            "label": v.label,
            "period_start": v.period_start.date().isoformat(),
            "period_end": v.period_end.date().isoformat(),
        }
        for v in versions
    ]
