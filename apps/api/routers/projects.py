from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user
from src.database.base import get_db
from src.database.models import User
from src.services.project_service import create_project, list_projects, project_dashboard

router = APIRouter(prefix="/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    name: str
    description: str | None = None
    technologies: list[str] | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None
    technologies: list[str] | None

    model_config = ConfigDict(from_attributes=True)


@router.post("", response_model=ProjectResponse, status_code=201)
def add_project(payload: CreateProjectRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProjectResponse:
    project = create_project(db, user.id, payload.name, payload.description, payload.technologies)
    return ProjectResponse.model_validate(project)


@router.get("", response_model=list[ProjectResponse])
def get_projects(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ProjectResponse]:
    return [ProjectResponse.model_validate(p) for p in list_projects(db, user.id)]


@router.get("/{project_id}/dashboard")
def get_project_dashboard(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    try:
        return project_dashboard(db, project_id)
    except ValueError:
        raise HTTPException(404, "Project not found")
