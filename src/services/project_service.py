"""Project CRUD + rollup analytics for the Project Analytics screen (section 12)."""
from __future__ import annotations

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
