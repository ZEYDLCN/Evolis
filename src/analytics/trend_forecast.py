"""Personal Trend Forecast — section 25.

A deterministic linear projection over the user's own trailing weekly
history — ordinary least squares, plain Python, no external stats
dependency and no LLM. This is a projection of "if the current trend
continues," not a prediction; the wording in TrendForecast.direction
and the confidence label both make that explicit.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.analytics.productivity import completion_rate, deep_work_hours_per_day
from src.analytics.temporal import period_bounds

LOOKBACK_WEEKS = 8
FLAT_SLOPE_THRESHOLD = 0.01  # relative to the metric's own scale; see _direction


@dataclass
class TrendForecast:
    metric: str
    history: list[float]  # oldest -> newest, one point per week
    forecast_next: float
    direction: str  # "up" | "down" | "flat"
    confidence: str  # "low" | "medium" | "high" — based on fit quality (r^2) and sample size

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "history": self.history,
            "forecast_next": self.forecast_next,
            "direction": self.direction,
            "confidence": self.confidence,
        }


def _linear_fit(values: list[float]) -> tuple[float, float, float]:
    """Ordinary least squares over x = 0..n-1. Returns (slope, intercept, r_squared)."""
    n = len(values)
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(values) / n

    ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values))
    ss_xx = sum((x - mean_x) ** 2 for x in xs)
    if ss_xx == 0:
        return 0.0, mean_y, 0.0

    slope = ss_xy / ss_xx
    intercept = mean_y - slope * mean_x

    ss_tot = sum((y - mean_y) ** 2 for y in values)
    if ss_tot == 0:
        return slope, intercept, 1.0 if slope == 0 else 0.0
    predicted = [intercept + slope * x for x in xs]
    ss_res = sum((y - p) ** 2 for y, p in zip(values, predicted))
    r_squared = max(0.0, 1 - ss_res / ss_tot)

    return slope, intercept, r_squared


def _direction(slope: float, values: list[float]) -> str:
    scale = max(abs(v) for v in values) or 1.0
    relative_slope = slope / scale
    if abs(relative_slope) < FLAT_SLOPE_THRESHOLD:
        return "flat"
    return "up" if slope > 0 else "down"


def _confidence(r_squared: float, n_points: int) -> str:
    if n_points < 4:
        return "low"
    if r_squared >= 0.5:
        return "high"
    if r_squared >= 0.2:
        return "medium"
    return "low"


def _weekly_history(db: Session, user_id: str, metric_fn, now: dt.datetime) -> list[float]:
    values = []
    for i in range(LOOKBACK_WEEKS - 1, -1, -1):
        anchor = (now - dt.timedelta(weeks=i)).date()
        start, end = period_bounds("weekly", anchor)
        values.append(metric_fn(db, user_id, start, end))
    return values


def forecast_completion_rate(db: Session, user_id: str, now: dt.datetime | None = None) -> TrendForecast:
    now = now or dt.datetime.utcnow()
    history = _weekly_history(db, user_id, lambda d, u, s, e: completion_rate(d, u, s, e)["completion_rate"], now)
    slope, intercept, r_squared = _linear_fit(history)
    forecast = round(min(1.0, max(0.0, intercept + slope * len(history))), 4)
    return TrendForecast(
        metric="completion_rate",
        history=[round(v, 4) for v in history],
        forecast_next=forecast,
        direction=_direction(slope, history),
        confidence=_confidence(r_squared, sum(1 for v in history if v != 0.0)),
    )


def forecast_deep_work(db: Session, user_id: str, now: dt.datetime | None = None) -> TrendForecast:
    now = now or dt.datetime.utcnow()
    history = _weekly_history(db, user_id, deep_work_hours_per_day, now)
    slope, intercept, r_squared = _linear_fit(history)
    forecast = round(max(0.0, intercept + slope * len(history)), 2)
    return TrendForecast(
        metric="deep_work_hours_per_day",
        history=[round(v, 2) for v in history],
        forecast_next=forecast,
        direction=_direction(slope, history),
        confidence=_confidence(r_squared, sum(1 for v in history if v != 0.0)),
    )
