"""Privacy — section 32: data export and account deletion.

Every table with a user_id column is included in both operations, so
neither one silently misses a table added later without a glance at this
file — the delete order matters (children before parents; entries' own
children before entries) and it's short enough to keep as an explicit list
rather than a "delete everything with a matching user_id" ORM cascade
across a dozen unrelated relationships.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import (
    Activity,
    Cluster,
    Embedding,
    Entry,
    EntryTopic,
    FocusSession,
    Goal,
    Insight,
    Project,
    Skill,
    Task,
    User,
    Version,
    VersionMetric,
)


def export_user_data(db: Session, user_id: str) -> dict:
    def _rows(model, **filters):
        return [
            {c.name: getattr(row, c.name) for c in model.__table__.columns}
            for row in db.query(model).filter_by(**filters).all()
        ]

    entry_ids = [e.id for e in db.query(Entry.id).filter(Entry.user_id == user_id)]
    version_ids = [v.id for v in db.query(Version.id).filter(Version.user_id == user_id)]

    return {
        "user": _rows(User, id=user_id)[0] if db.get(User, user_id) else None,
        "entries": _rows(Entry, user_id=user_id),
        "entry_topics": [r for eid in entry_ids for r in _rows(EntryTopic, entry_id=eid)],
        "activities": [r for eid in entry_ids for r in _rows(Activity, entry_id=eid)],
        "embeddings": [r for eid in entry_ids for r in _rows(Embedding, entry_id=eid)],
        "projects": _rows(Project, user_id=user_id),
        "tasks": _rows(Task, user_id=user_id),
        "skills": _rows(Skill, user_id=user_id),
        "goals": _rows(Goal, user_id=user_id),
        "clusters": _rows(Cluster, user_id=user_id),
        "focus_sessions": _rows(FocusSession, user_id=user_id),
        "insights": _rows(Insight, user_id=user_id),
        "versions": _rows(Version, user_id=user_id),
        "version_metrics": [r for vid in version_ids for r in _rows(VersionMetric, version_id=vid)],
    }


def delete_user_account(db: Session, user_id: str) -> None:
    entry_ids = [row[0] for row in db.execute(select(Entry.id).where(Entry.user_id == user_id))]
    version_ids = [row[0] for row in db.execute(select(Version.id).where(Version.user_id == user_id))]

    if entry_ids:
        db.query(EntryTopic).filter(EntryTopic.entry_id.in_(entry_ids)).delete(synchronize_session=False)
        db.query(Activity).filter(Activity.entry_id.in_(entry_ids)).delete(synchronize_session=False)
        db.query(Embedding).filter(Embedding.entry_id.in_(entry_ids)).delete(synchronize_session=False)
    if version_ids:
        db.query(VersionMetric).filter(VersionMetric.version_id.in_(version_ids)).delete(synchronize_session=False)

    db.query(Task).filter(Task.user_id == user_id).delete(synchronize_session=False)
    db.query(Cluster).filter(Cluster.user_id == user_id).delete(synchronize_session=False)
    db.query(Skill).filter(Skill.user_id == user_id).delete(synchronize_session=False)
    db.query(Goal).filter(Goal.user_id == user_id).delete(synchronize_session=False)
    db.query(FocusSession).filter(FocusSession.user_id == user_id).delete(synchronize_session=False)
    db.query(Insight).filter(Insight.user_id == user_id).delete(synchronize_session=False)
    db.query(Version).filter(Version.user_id == user_id).delete(synchronize_session=False)
    db.query(Entry).filter(Entry.user_id == user_id).delete(synchronize_session=False)
    db.query(Project).filter(Project.user_id == user_id).delete(synchronize_session=False)
    db.query(User).filter(User.id == user_id).delete(synchronize_session=False)

    db.commit()
