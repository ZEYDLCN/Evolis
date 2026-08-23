"""Knowledge Graph — section 25 (optional). GET /graph/export always works
(pure computed JSON); POST /graph/sync only does something when NEO4J_URI
is configured, and says so either way rather than pretending it synced.
"""
import datetime as dt

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user
from src.database.base import get_db
from src.database.models import User
from src.graph.knowledge_graph import build_user_graph
from src.graph.neo4j_sync import neo4j_configured, sync_to_neo4j

router = APIRouter(prefix="/graph", tags=["graph"])


def _default_range(months: int) -> tuple[dt.datetime, dt.datetime]:
    end = dt.datetime.utcnow()
    start = end - dt.timedelta(days=30 * months)
    return start, end


@router.get("/export")
def export_graph(months: int = Query(6, ge=1, le=36), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    start, end = _default_range(months)
    return build_user_graph(db, user.id, start, end).to_dict()


@router.post("/sync")
def sync_graph(months: int = Query(6, ge=1, le=36), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    if not neo4j_configured():
        return {"synced": False, "reason": "NEO4J_URI not configured"}

    start, end = _default_range(months)
    graph = build_user_graph(db, user.id, start, end)
    synced = sync_to_neo4j(graph)
    return {"synced": synced, "nodes": len(graph.nodes), "relationships": len(graph.relationships)}
