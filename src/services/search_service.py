"""Personal Search — section 14.

Deterministic substring search across a user's own entries, projects,
topics, skills, and versions. This is a literal "find my stuff" tool, not
semantic retrieval — see src/rag/retriever.py for the embedding-based
search used by Ask Evolis. No LLM involved.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.encryption import encryption_enabled
from src.database.models import Entry, EntryTopic, Project, Skill, Version

MAX_RESULTS_PER_CATEGORY = 6
SNIPPET_RADIUS = 40


def _snippet(text: str, query: str) -> str:
    idx = text.lower().find(query.lower())
    if idx == -1:
        return text[: SNIPPET_RADIUS * 2]
    start = max(0, idx - SNIPPET_RADIUS)
    end = min(len(text), idx + len(query) + SNIPPET_RADIUS)
    return f"{'…' if start > 0 else ''}{text[start:end]}{'…' if end < len(text) else ''}"


def _search_entries(
    db: Session, user_id: str, query: str, start: dt.datetime | None = None, end: dt.datetime | None = None, topic: str | None = None
) -> list[dict]:
    """Entry Search Filters (section 34): narrow by date range and/or topic
    on top of the text match. Filters are applied in Python alongside the
    encrypted-text path so the same code handles both storage modes."""
    entry_ids_for_topic: set[str] | None = None
    if topic:
        rows = (
            db.query(EntryTopic.entry_id)
            .join(Entry, Entry.id == EntryTopic.entry_id)
            .filter(Entry.user_id == user_id, EntryTopic.topic == topic)
            .all()
        )
        entry_ids_for_topic = {r[0] for r in rows}
        if not entry_ids_for_topic:
            return []

    base_query = db.query(Entry).filter(Entry.user_id == user_id)
    if start is not None:
        base_query = base_query.filter(Entry.entry_date >= start)
    if end is not None:
        base_query = base_query.filter(Entry.entry_date < end)
    if entry_ids_for_topic is not None:
        base_query = base_query.filter(Entry.id.in_(entry_ids_for_topic))
    base_query = base_query.order_by(Entry.entry_date.desc())

    if encryption_enabled():
        # raw_text is ciphertext in the database — decrypt this user's own
        # rows (the ORM does this transparently) and filter in Python.
        # See src/database/encryption.py and rag/retriever.py's keyword_search.
        needle = query.lower()
        rows = base_query.all()
        matches = [e for e in rows if needle in e.raw_text.lower()][:MAX_RESULTS_PER_CATEGORY]
    else:
        like = f"%{query}%"
        matches = base_query.filter(Entry.raw_text.ilike(like)).limit(MAX_RESULTS_PER_CATEGORY).all()

    return [{"id": e.id, "date": e.entry_date.date().isoformat(), "snippet": _snippet(e.raw_text, query)} for e in matches]


def search_all(
    db: Session,
    user_id: str,
    query: str,
    start: dt.datetime | None = None,
    end: dt.datetime | None = None,
    topic: str | None = None,
) -> dict:
    q = query.strip()
    if not q:
        return {"entries": [], "projects": [], "topics": [], "skills": [], "versions": []}

    like = f"%{q}%"

    projects = (
        db.query(Project).filter(Project.user_id == user_id, Project.name.ilike(like)).limit(MAX_RESULTS_PER_CATEGORY).all()
    )
    topic_rows = db.execute(
        select(EntryTopic.topic)
        .join(Entry, Entry.id == EntryTopic.entry_id)
        .where(Entry.user_id == user_id, EntryTopic.topic.ilike(like))
        .distinct()
        .limit(MAX_RESULTS_PER_CATEGORY)
    ).all()
    skills = db.query(Skill).filter(Skill.user_id == user_id, Skill.name.ilike(like)).limit(MAX_RESULTS_PER_CATEGORY).all()
    versions = (
        db.query(Version).filter(Version.user_id == user_id, Version.label.ilike(like)).limit(MAX_RESULTS_PER_CATEGORY).all()
    )

    return {
        "entries": _search_entries(db, user_id, q, start, end, topic),
        "projects": [{"id": p.id, "name": p.name} for p in projects],
        "topics": [t for (t,) in topic_rows],
        "skills": [{"id": s.id, "name": s.name} for s in skills],
        "versions": [{"id": v.id, "label": v.label} for v in versions],
    }
