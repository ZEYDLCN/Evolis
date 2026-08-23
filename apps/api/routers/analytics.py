import datetime as dt

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from apps.api.dependencies import get_current_user
from src.analytics.anomalies import detect_learning_time_anomalies
from src.analytics.interests import topic_interest_scores
from src.analytics.onboarding import compute_onboarding_status
from src.analytics.patterns import detect_project_load_vs_completion
from src.analytics.productivity import behavior_summary
from src.analytics.skill_graph import build_skill_graph
from src.analytics.skills import skill_scores
from src.analytics.streaks import compute_heatmap, compute_streak
from src.database.base import get_db
from src.database.models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _default_range(months: int) -> tuple[dt.datetime, dt.datetime]:
    end = dt.datetime.utcnow()
    start = end - dt.timedelta(days=30 * months)
    return start, end


@router.get("/interests")
def get_interests(months: int = Query(3, ge=1, le=36), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    start, end = _default_range(months)
    return topic_interest_scores(db, user.id, start, end)


@router.get("/skills")
def get_skills(months: int = Query(3, ge=1, le=36), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    start, end = _default_range(months)
    return skill_scores(db, user.id, start, end)


@router.get("/behavior")
def get_behavior(months: int = Query(3, ge=1, le=36), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    start, end = _default_range(months)
    return behavior_summary(db, user.id, start, end)


@router.get("/skill-graph")
def get_skill_graph(months: int = Query(6, ge=1, le=36), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    start, end = _default_range(months)
    return build_skill_graph(db, user.id, start, end)


@router.get("/anomalies")
def get_anomalies(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    anomalies = detect_learning_time_anomalies(db, user.id)
    return [
        {
            "metric": a.metric,
            "current_value": a.current_value,
            "baseline_mean": round(a.baseline_mean, 1),
            "z_score": round(a.z_score, 2),
            "ratio": round(a.ratio, 2) if a.baseline_mean else None,
        }
        for a in anomalies
    ]


@router.get("/patterns")
def get_patterns(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    finding = detect_project_load_vs_completion(db, user.id)
    if not finding:
        return []
    return [
        {
            "correlation": finding.correlation,
            "weeks_observed": finding.weeks_observed,
            "description": finding.description,
        }
    ]


@router.get("/streak")
def get_streak(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    streak = compute_streak(db, user.id)
    return {
        "current_streak": streak.current_streak,
        "longest_streak": streak.longest_streak,
        "last_entry_date": streak.last_entry_date.isoformat() if streak.last_entry_date else None,
        "is_new_best": streak.is_new_best,
    }


@router.get("/heatmap")
def get_heatmap(days: int = Query(365, ge=7, le=730), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    return compute_heatmap(db, user.id, days=days)


@router.get("/onboarding")
def get_onboarding(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return compute_onboarding_status(db, user.id).to_dict()
