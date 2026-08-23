from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from apps.api.dependencies import get_current_user
from sqlalchemy.orm import Session

from src.database.base import get_db
from src.database.models import User
from src.services.task_service import complete_task, create_task, list_tasks

router = APIRouter(prefix="/tasks", tags=["tasks"])


class CreateTaskRequest(BaseModel):
    title: str
    project_id: str | None = None
    entry_id: str | None = None


class TaskResponse(BaseModel):
    id: str
    title: str
    status: str
    project_id: str | None
    created_at: str | None = None
    completed_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


def _serialize(task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        title=task.title,
        status=task.status,
        project_id=task.project_id,
        created_at=task.created_at.isoformat() if task.created_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
    )


@router.post("", response_model=TaskResponse, status_code=201)
def add_task(payload: CreateTaskRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TaskResponse:
    task = create_task(db, user.id, payload.title, payload.project_id, payload.entry_id)
    return _serialize(task)


@router.get("", response_model=list[TaskResponse])
def get_tasks(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[TaskResponse]:
    return [_serialize(t) for t in list_tasks(db, user.id)]


@router.post("/{task_id}/complete", response_model=TaskResponse)
def mark_task_complete(task_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TaskResponse:
    task = complete_task(db, user.id, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return _serialize(task)
