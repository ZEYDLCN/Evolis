"""Orchestrates the ingestion pipeline for a single daily entry:

Natural Language Entry -> LLM Structured Extraction -> PostgreSQL
    -> Embedding Generation -> (clustering happens asynchronously, see
       src/services/project_service.py + worker tasks)
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from src.database.models import Activity, Embedding, Entry, EntryTopic, ExtractionFeedback, Project
from src.embeddings.embedding_service import get_embedding_model
from src.extraction.llm_extractor import get_extractor
from src.monitoring.metrics import track_embedding_generation


def create_entry(db: Session, user_id: str, raw_text: str, entry_date: dt.date | None = None) -> Entry:
    extractor = get_extractor()
    extracted = extractor.extract(raw_text)

    entry = Entry(
        user_id=user_id,
        raw_text=raw_text,
        entry_date=dt.datetime.combine(entry_date, dt.time.min) if entry_date else dt.datetime.utcnow(),
        completion_status=extracted.completion_status,
        blockers=extracted.blockers,
        extraction_raw=extracted.model_dump(),
    )
    db.add(entry)
    db.flush()

    for topic in extracted.topics:
        db.add(EntryTopic(entry_id=entry.id, topic=topic))

    for activity in extracted.activities:
        project_id = None
        if activity.project:
            project_id = _resolve_or_create_project(db, user_id, activity.project)
        db.add(
            Activity(
                entry_id=entry.id,
                type=activity.type,
                topic=activity.topic,
                project_id=project_id,
                duration_minutes=activity.duration_minutes,
            )
        )

    model = get_embedding_model()
    with track_embedding_generation():
        vector = model.embed(raw_text)
    db.add(Embedding(entry_id=entry.id, model_name=model.name, vector=vector))

    db.commit()
    db.refresh(entry)
    return entry


def correct_entry_extraction(db: Session, user_id: str, entry_id: str, corrected: dict) -> Entry | None:
    """Apply a user's correction to an entry's AI extraction (section 20)
    and store the before/after pair as ground truth for a future eval
    dataset (section 21, src.database.models.ExtractionFeedback).

    `corrected` may include any of "topics" (list[str]), "completion_status"
    (str | None), and "activities" (list of {type, topic, duration_minutes,
    project}) — only the keys present are changed.
    """
    entry = db.query(Entry).filter(Entry.id == entry_id, Entry.user_id == user_id).first()
    if not entry:
        return None

    db.add(
        ExtractionFeedback(
            entry_id=entry.id,
            user_id=user_id,
            original_extraction=entry.extraction_raw or {},
            corrected_extraction=corrected,
        )
    )

    if "completion_status" in corrected:
        entry.completion_status = corrected["completion_status"]

    if "topics" in corrected:
        db.query(EntryTopic).filter(EntryTopic.entry_id == entry.id).delete()
        for topic in corrected["topics"]:
            db.add(EntryTopic(entry_id=entry.id, topic=topic))

    if "activities" in corrected:
        db.query(Activity).filter(Activity.entry_id == entry.id).delete()
        for activity in corrected["activities"]:
            project_id = None
            if activity.get("project"):
                project_id = _resolve_or_create_project(db, user_id, activity["project"])
            db.add(
                Activity(
                    entry_id=entry.id,
                    type=activity.get("type") or "project_development",
                    topic=activity.get("topic"),
                    project_id=project_id,
                    duration_minutes=activity.get("duration_minutes"),
                )
            )

    # Keep extraction_raw's summary fields in sync so GET /entries reflects
    # the corrected state, not the original AI guess.
    if entry.extraction_raw:
        merged = dict(entry.extraction_raw)
        if "topics" in corrected:
            merged["topics"] = corrected["topics"]
        if "completion_status" in corrected:
            merged["completion_status"] = corrected["completion_status"]
        entry.extraction_raw = merged

    db.commit()
    db.refresh(entry)
    return entry


def _resolve_or_create_project(db: Session, user_id: str, name: str) -> str:
    project = db.query(Project).filter(Project.user_id == user_id, Project.name == name).first()
    if project:
        return project.id
    project = Project(user_id=user_id, name=name)
    db.add(project)
    db.flush()
    return project.id
