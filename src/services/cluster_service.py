"""Rebuilds semantic topic clusters for a user (sections 8-9).

    Entries -> Embeddings -> HDBSCAN -> Clusters (persisted) -> LLM naming

Runs as a background job (apps/worker/tasks.py::rebuild_clusters) but is
plain, synchronous, DB-session-taking code so it's also directly unit- and
integration-testable without Celery.
"""
from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from src.database.models import Cluster, Embedding, Entry, EntryTopic
from src.ml.clustering.hdbscan_cluster import cluster_embeddings
from src.ml.clustering.naming import name_cluster

MIN_CLUSTER_SIZE = 3


def rebuild_clusters_for_user(db: Session, user_id: str) -> list[Cluster]:
    rows = (
        db.query(Embedding.entry_id, Embedding.vector)
        .join(Entry, Entry.id == Embedding.entry_id)
        .filter(Entry.user_id == user_id)
        .all()
    )
    if len(rows) < MIN_CLUSTER_SIZE:
        return []

    entry_ids = [r[0] for r in rows]
    vectors = [r[1] for r in rows]

    assignment = cluster_embeddings(vectors, min_cluster_size=MIN_CLUSTER_SIZE)
    if assignment is None:
        return []

    # Wipe this user's previous cluster assignments before re-labeling —
    # cluster identities aren't stable across rebuilds (HDBSCAN doesn't
    # guarantee the same label means the same thing twice).
    db.query(EntryTopic).filter(
        EntryTopic.entry_id.in_(entry_ids), EntryTopic.cluster_id.is_not(None)
    ).update({EntryTopic.cluster_id: None}, synchronize_session=False)
    db.query(Cluster).filter(Cluster.user_id == user_id).delete(synchronize_session=False)

    entries_by_label: dict[int, list[str]] = defaultdict(list)
    for entry_id, label in zip(entry_ids, assignment.labels):
        if label == -1:  # noise point, per HDBSCAN convention
            continue
        entries_by_label[label].append(entry_id)

    created: list[Cluster] = []
    for label, member_entry_ids in entries_by_label.items():
        topics = (
            db.query(EntryTopic)
            .filter(EntryTopic.entry_id.in_(member_entry_ids))
            .all()
        )
        topic_names = [t.topic for t in topics]
        representative_texts = [
            e.raw_text for e in db.query(Entry).filter(Entry.id.in_(member_entry_ids[:5])).all()
        ]

        cluster = Cluster(
            user_id=user_id,
            label=name_cluster(representative_texts, topic_names),
            representative_topics=sorted(set(topic_names))[:10],
        )
        db.add(cluster)
        db.flush()

        for topic_row in topics:
            topic_row.cluster_id = cluster.id

        created.append(cluster)

    db.commit()
    return created


def list_clusters(db: Session, user_id: str) -> list[Cluster]:
    return db.query(Cluster).filter(Cluster.user_id == user_id).all()
