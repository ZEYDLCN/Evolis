from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user
from src.database.base import get_db
from src.database.models import Activity, Entry, User, Version
from src.versions.diff import diff_versions
from src.versions.release_notes import render_release_notes
from src.versions.snapshot import version_metrics_dict

router = APIRouter(tags=["diff"])


def _get_versions(db: Session, user: User, base: str, target: str) -> tuple[Version, Version]:
    base_version = db.query(Version).filter(Version.user_id == user.id, Version.label == base).first()
    target_version = db.query(Version).filter(Version.user_id == user.id, Version.label == target).first()
    if not base_version or not target_version:
        raise HTTPException(404, "One or both versions not found")
    return base_version, target_version


@router.get("/diff")
def get_diff(
    base: str = Query(..., description="Base version label, e.g. '1.2'"),
    target: str = Query(..., description="Target version label, e.g. '1.7'"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    base_version, target_version = _get_versions(db, user, base, target)
    diff = diff_versions(version_metrics_dict(base_version), version_metrics_dict(target_version))
    return {"base": base, "target": target, **diff.to_dict()}


@router.get("/release-notes")
def get_release_notes(
    base: str = Query(...),
    target: str = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    base_version, target_version = _get_versions(db, user, base, target)
    diff = diff_versions(version_metrics_dict(base_version), version_metrics_dict(target_version))

    active_projects = (
        db.query(Activity.project_id)
        .join(Entry, Entry.id == Activity.entry_id)
        .filter(
            Entry.user_id == user.id,
            Entry.entry_date >= target_version.period_start,
            Entry.entry_date < target_version.period_end,
            Activity.project_id.is_not(None),
        )
        .distinct()
        .count()
    )
    return render_release_notes(base, target, diff, active_project_count=active_projects)
