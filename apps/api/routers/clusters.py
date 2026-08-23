"""Semantic topic clusters — sections 8-9.

Rebuilding is synchronous here for the MVP (fine at low entry counts); once
a user has enough history, dispatch apps.worker.tasks.rebuild_clusters
instead of calling this inline.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user
from src.database.base import get_db
from src.database.models import User
from src.services.cluster_service import list_clusters, rebuild_clusters_for_user

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.post("/rebuild")
def rebuild(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    clusters = rebuild_clusters_for_user(db, user.id)
    return [{"id": c.id, "label": c.label, "representative_topics": c.representative_topics} for c in clusters]


@router.get("")
def get_clusters(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    return [{"id": c.id, "label": c.label, "representative_topics": c.representative_topics} for c in list_clusters(db, user.id)]
