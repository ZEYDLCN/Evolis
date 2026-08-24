"""Turning Point Detector — the data-detected half of "Evolution Forks".

No ML needed for a first version: a rolling window comparison of the
user's weekly topic-interest vector is enough to flag a real distribution
shift. For each week boundary in the lookback range, compare the average
interest vector over the WINDOW_WEEKS before it against WINDOW_WEEKS
after, score the shift, and surface the single highest-scoring boundary
per non-overlapping segment as a *candidate* — never persisted on its
own. A candidate only becomes a real timeline event
(src.database.models.EvolutionEvent) when the user explicitly confirms
it via POST /evolution-events, per the product's core rule here: Evolis
notices a shift, it never announces "this is what changed your life."
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from src.analytics.interests import topic_interest_scores
from src.analytics.temporal import period_bounds

LOOKBACK_WEEKS = 16
WINDOW_WEEKS = 4
MIN_SHIFT_SCORE = 0.35  # sum of |after - before| across topics, half-normalized


@dataclass
class TurningPointCandidate:
    week_start: dt.date
    shift_score: float
    metrics_before: dict[str, float]
    metrics_after: dict[str, float]
    new_topics: list[str] = field(default_factory=list)
    faded_topics: list[str] = field(default_factory=list)

    @property
    def confidence(self) -> str:
        if self.shift_score >= 0.7:
            return "high"
        if self.shift_score >= 0.5:
            return "medium"
        return "low"

    def to_dict(self) -> dict:
        return {
            "week_start": self.week_start.isoformat(),
            "shift_score": round(self.shift_score, 3),
            "confidence": self.confidence,
            "metrics_before": self.metrics_before,
            "metrics_after": self.metrics_after,
            "new_topics": self.new_topics,
            "faded_topics": self.faded_topics,
        }


def _window_vector(db: Session, user_id: str, start: dt.date, weeks: int) -> dict[str, float]:
    window_start, _ = period_bounds("weekly", start)
    window_end = window_start + dt.timedelta(weeks=weeks)
    return topic_interest_scores(db, user_id, window_start, window_end)


def _shift_score(before: dict[str, float], after: dict[str, float]) -> float:
    topics = set(before) | set(after)
    if not topics:
        return 0.0
    total = sum(abs(after.get(t, 0.0) - before.get(t, 0.0)) for t in topics)
    return total / len(topics) / 0.5  # normalize: a max-possible per-topic swing of 1.0 -> score ~2; /0.5 keeps typical shifts in a legible 0-1ish range


def detect_turning_point_candidates(
    db: Session, user_id: str, now: dt.datetime | None = None, existing_dates: set[dt.date] | None = None
) -> list[TurningPointCandidate]:
    """Returns the best-scoring shift boundary per non-overlapping segment
    of the lookback window. `existing_dates` lets a caller exclude weeks
    already covered by a confirmed EvolutionEvent so re-running doesn't
    keep re-suggesting the same moment."""
    now = now or dt.datetime.utcnow()
    existing_dates = existing_dates or set()
    today = now.date()
    lookback_start_dt, _ = period_bounds("weekly", today - dt.timedelta(weeks=LOOKBACK_WEEKS))
    lookback_start = lookback_start_dt.date()

    candidates: list[TurningPointCandidate] = []
    cursor = lookback_start
    segment_end = today - dt.timedelta(weeks=WINDOW_WEEKS)  # need WINDOW_WEEKS of "after" data past the boundary

    while cursor <= segment_end:
        before = _window_vector(db, user_id, cursor - dt.timedelta(weeks=WINDOW_WEEKS), WINDOW_WEEKS)
        after = _window_vector(db, user_id, cursor, WINDOW_WEEKS)
        score = _shift_score(before, after)

        # An empty "before" window isn't a turning point, just the user
        # having started journaling — nothing to shift away from yet.
        if before and score >= MIN_SHIFT_SCORE and cursor not in existing_dates:
            new_topics = sorted((t for t in after if after[t] >= 0.15 and before.get(t, 0.0) < 0.15), key=lambda t: -after[t])
            faded_topics = sorted((t for t in before if before[t] >= 0.15 and after.get(t, 0.0) < 0.15), key=lambda t: -before[t])
            candidates.append(
                TurningPointCandidate(
                    week_start=cursor,
                    shift_score=score,
                    metrics_before=before,
                    metrics_after=after,
                    new_topics=new_topics[:3],
                    faded_topics=faded_topics[:3],
                )
            )

        cursor += dt.timedelta(weeks=WINDOW_WEEKS)

    candidates.sort(key=lambda c: c.shift_score, reverse=True)
    return candidates[:5]
