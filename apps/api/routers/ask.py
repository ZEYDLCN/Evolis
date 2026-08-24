from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user, get_lang
from src.agents.orchestrator import ask
from src.database.base import get_db
from src.database.models import User

router = APIRouter(prefix="/ask", tags=["ask"])


class AskRequest(BaseModel):
    question: str


@router.post("")
def ask_evolis(
    payload: AskRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db), lang: str = Depends(get_lang)
) -> dict:
    return ask(db, user.id, payload.question, lang)
