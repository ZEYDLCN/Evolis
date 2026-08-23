from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user
from src.database.base import get_db
from src.database.models import User, Version
from src.versions.diff import diff_versions
from src.versions.snapshot import version_metrics_dict

router = APIRouter(tags=["diff"])


@router.get("/diff")
def get_diff(
    base: str = Query(..., description="Base version label, e.g. '1.2'"),
    target: str = Query(..., description="Target version label, e.g. '1.7'"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    base_version = db.query(Version).filter(Version.user_id == user.id, Version.label == base).first()
    target_version = db.query(Version).filter(Version.user_id == user.id, Version.label == target).first()
    if not base_version or not target_version:
        raise HTTPException(404, "One or both versions not found")

    diff = diff_versions(version_metrics_dict(base_version), version_metrics_dict(target_version))
    return {"base": base, "target": target, **diff.to_dict()}
