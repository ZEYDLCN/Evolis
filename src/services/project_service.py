"""Project CRUD + rollup analytics for the Project Analytics / Project Detail
screens (sections 12, 15)."""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from src.database.models import Activity, Entry, Project


def create_project(db: Session, user_id: str, name: str, description: str | None = None, technologies: list[str] | None = None) -> Project:
    project = Project(user_id=user_id, name=name, description=description, technologies=technologies or [])
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def list_projects(db: Session, user_id: str) -> list[Project]:
    return db.query(Project).filter(Project.user_id == user_id).all()


def project_dashboard(db: Session, project_id: str) -> dict:
    project = db.get(Project, project_id)
    if not project:
        raise ValueError("project not found")

    rows = db.execute(
        select(Entry.entry_date, Activity.duration_minutes)
        .join(Activity, Activity.entry_id == Entry.id)
        .where(Activity.project_id == project_id)
    ).all()

    active_days = len({r[0].date() for r in rows})
    total_sessions = len(rows)
    focus_minutes = sum(r[1] or 0 for r in rows)

    return {
        "project": project.name,
        "active_days": active_days,
        "total_sessions": total_sessions,
        "estimated_focus_hours": round(focus_minutes / 60, 1),
        "main_technologies": project.technologies or [],
    }


def project_detail(db: Session, user_id: str, project_id: str) -> dict:
    """Full Project Detail Dashboard payload (section 15): rollup metrics
    plus a weekly focus-hours trend and a timeline of recent entries that
    touched this project — everything computed, nothing LLM-generated."""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise ValueError("project not found")

    rows = db.execute(
        select(Entry.id, Entry.entry_date, Entry.raw_text, Activity.type, Activity.topic, Activity.duration_minutes)
        .join(Activity, Activity.entry_id == Entry.id)
        .where(Activity.project_id == project_id)
        .order_by(Entry.entry_date.desc())
    ).all()

    active_days = len({r[1].date() for r in rows})
    total_sessions = len(rows)
    focus_minutes = sum(r[5] or 0 for r in rows)
    topics_touched = sorted({r[4] for r in rows if r[4]})

    # Weekly focus-hours trend, oldest -> newest, last 8 ISO weeks with activity.
    weekly_minutes: dict[str, int] = defaultdict(int)
    for _, entry_date, *_rest, minutes in rows:
        iso_year, iso_week, _ = entry_date.isocalendar()
        weekly_minutes[f"{iso_year}-W{iso_week:02d}"] += minutes or 0
    focus_trend = [
        {"week": week, "hours": round(minutes / 60, 1)} for week, minutes in sorted(weekly_minutes.items())[-8:]
    ]

    # Timeline: one row per distinct entry that touched this project.
    seen_entries: set[str] = set()
    timeline: list[dict] = []
    for entry_id, entry_date, raw_text, activity_type, topic, minutes in rows:
        if entry_id in seen_entries:
            continue
        seen_entries.add(entry_id)
        timeline.append(
            {
                "entry_id": entry_id,
                "date": entry_date.date().isoformat(),
                "snippet": raw_text[:140],
                "topic": topic,
                "duration_minutes": minutes,
            }
        )
        if len(timeline) >= 20:
            break

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "technologies": project.technologies or [],
        "active_days": active_days,
        "total_sessions": total_sessions,
        "estimated_focus_hours": round(focus_minutes / 60, 1),
        "topics_touched": topics_touched,
        "focus_trend": focus_trend,
        "timeline": timeline,
    }
