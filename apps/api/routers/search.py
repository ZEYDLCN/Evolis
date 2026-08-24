from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user
from src.database.base import get_db
from src.database.models import User
from src.services.search_service import search_all

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(q: str = "", user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return search_all(db, user.id, q)
