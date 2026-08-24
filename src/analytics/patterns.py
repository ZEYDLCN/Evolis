"""Pattern Detection — section 16.

Looks for recurring associations between behavioral metrics across weekly
buckets (e.g. "active project count" vs "completion rate"). Deliberately
reports correlation, never causation — see PatternFinding.description, which
never uses cause/effect language.
"""
from __future__ import annotations

import datetime as dt
import statistics
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.analytics.productivity import completion_rate
from src.analytics.temporal import period_bounds
from src.database.models import Activity, Entry

LOOKBACK_WEEKS = 12
MIN_WEEKS_FOR_CORRELATION = 4
NOTABLE_CORRELATION = 0.4  # |r| below this isn't worth surfacing


@dataclass
class PatternFinding:
    metric_a: str
    metric_b: str
    correlation: float
    weeks_observed: int

    @property
    def confidence(self) -> str:
        """Insight Confidence (section 54): a caller only ever sees a
        finding that already cleared NOTABLE_CORRELATION, so this reflects
        sample size and correlation strength together rather than
        re-deciding whether to surface it at all."""
        if self.weeks_observed >= 8 and abs(self.correlation) >= 0.6:
            return "high"
        if self.weeks_observed >= MIN_WEEKS_FOR_CORRELATION:
            return "medium"
        return "low"

    def description(self, lang: str = "en") -> str:
        if lang == "tr":
            direction = "yükseldiği dönemlerde" if self.correlation > 0 else "düştüğü dönemlerde"
            other_direction = "yükseliyor" if self.correlation > 0 else "düşüyor"
            metric_a_tr = "Aktif proje sayısının" if self.metric_a == "active project count" else self.metric_a
            metric_b_tr = "completion rate" if self.metric_b == "completion rate" else self.metric_b
            return (
                f"{metric_a_tr} {direction} {metric_b_tr} genellikle {other_direction} "
                f"gözlemleniyor (korelasyon: {self.correlation:.2f}, {self.weeks_observed} hafta üzerinden). "
                "Bu bir neden-sonuç iddiası değil, birlikte-görülme (association) gözlemidir."
            )
        direction = "rises" if self.correlation > 0 else "falls"
        other_direction = "rises" if self.correlation > 0 else "falls"
        return (
            f"When {self.metric_a} {direction}, {self.metric_b} usually {other_direction} too "
            f"(correlation: {self.correlation:.2f}, over {self.weeks_observed} weeks). "
            "This is an association, not a cause-and-effect claim."
        )


def _active_project_count(db: Session, user_id: str, start: dt.datetime, end: dt.datetime) -> int:
    rows = db.execute(
        select(Activity.project_id)
        .join(Entry, Entry.id == Activity.entry_id)
        .where(Entry.user_id == user_id, Entry.entry_date >= start, Entry.entry_date < end, Activity.project_id.is_not(None))
        .distinct()
    ).all()
    return len(rows)


def detect_project_load_vs_completion(db: Session, user_id: str, now: dt.datetime | None = None) -> PatternFinding | None:
    now = now or dt.datetime.utcnow()
    project_counts: list[float] = []
    completion_rates: list[float] = []

    for i in range(LOOKBACK_WEEKS):
        anchor = (now - dt.timedelta(weeks=i)).date()
        start, end = period_bounds("weekly", anchor)
        completion = completion_rate(db, user_id, start, end)
        if completion["created"] == 0:
            continue  # no activity that week — not a data point either way
        project_counts.append(float(_active_project_count(db, user_id, start, end)))
        completion_rates.append(completion["completion_rate"])

    if len(project_counts) < MIN_WEEKS_FOR_CORRELATION or len(set(project_counts)) < 2 or len(set(completion_rates)) < 2:
        return None

    r = statistics.correlation(project_counts, completion_rates)
    if abs(r) < NOTABLE_CORRELATION:
        return None

    return PatternFinding(
        metric_a="active project count",
        metric_b="completion rate",
        correlation=round(r, 3),
        weeks_observed=len(project_counts),
    )
