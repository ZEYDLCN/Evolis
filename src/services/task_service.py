"""Task CRUD — backs the "Created Tasks / Completed Tasks" completion-rate
signal from section 13. Entirely optional for a user: see
src/analytics/productivity.py for the fallback when no tasks exist yet.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from src.database.models import Task


def create_task(db: Session, user_id: str, title: str, project_id: str | None = None, entry_id: str | None = None) -> Task:
    task = Task(user_id=user_id, title=title, project_id=project_id, entry_id=entry_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def complete_task(db: Session, user_id: str, task_id: str) -> Task | None:
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        return None
    task.status = "done"
    task.completed_at = dt.datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task


def list_tasks(db: Session, user_id: str) -> list[Task]:
    return db.query(Task).filter(Task.user_id == user_id).order_by(Task.created_at.desc()).all()
