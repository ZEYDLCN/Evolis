"""Background jobs — section 33: embedding generation, cluster rebuild,
version snapshots, monthly insights.

Embedding generation itself already happens synchronously in
src/services/entry_service.py for MVP simplicity; the task here exists for
when that gets moved off the request path (e.g. once a hosted embedding API
introduces real latency).
"""
from __future__ import annotations

import datetime as dt

from apps.worker.celery_app import celery_app
from src.database.base import session_scope
from src.database.models import Embedding, Entry, User
from src.embeddings.embedding_service import get_embedding_model
from src.ml.clustering.hdbscan_cluster import cluster_embeddings
from src.versions.snapshot import generate_version


@celery_app.task
def embed_entry(entry_id: str) -> None:
    with session_scope() as db:
        entry = db.get(Entry, entry_id)
        if not entry or entry.embedding:
            return
        model = get_embedding_model()
        vector = model.embed(entry.raw_text)
        db.add(Embedding(entry_id=entry.id, model_name=model.name, vector=vector))


@celery_app.task
def rebuild_clusters(user_id: str) -> None:
    with session_scope() as db:
        rows = (
            db.query(Embedding.entry_id, Embedding.vector)
            .join(Entry, Entry.id == Embedding.entry_id)
            .filter(Entry.user_id == user_id)
            .all()
        )
        if len(rows) < 3:
            return
        vectors = [r[1] for r in rows]
        cluster_embeddings(vectors)
        # Persisting Cluster/EntryTopic.cluster_id assignments is a follow-up
        # step once topic-name resolution (LLM naming, section 9) is wired in.


@celery_app.task
def generate_monthly_snapshots() -> None:
    today = dt.date.today()
    if today.day != 1:
        return  # only run on month boundaries

    with session_scope() as db:
        for (user_id,) in db.query(User.id).all():
            end = dt.datetime.combine(today, dt.time.min)
            start = dt.datetime(end.year, end.month - 1, 1) if end.month > 1 else dt.datetime(end.year - 1, 12, 1)
            generate_version(db, user_id, start, end)
