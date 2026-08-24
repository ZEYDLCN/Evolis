"""Dashboard summary — one aggregate payload for the Overview screen instead
of the frontend firing off ~8 separate requests. Every number here is
computed by the same deterministic analytics functions used elsewhere
(LLM != Analytics Engine still holds); this module's only job is picking
which of them are worth leading with and phrasing the one-line hero/insight
text from real deltas, never a free-floating LLM guess.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from src.analytics.anomalies import detect_learning_time_anomalies
from src.analytics.evolis_score import compute_evolis_score
from src.analytics.interests import topic_interest_scores
from src.analytics.patterns import detect_project_load_vs_completion
from src.analytics.productivity import behavior_summary
from src.analytics.streaks import compute_streak
from src.analytics.temporal import period_bounds
from src.database.models import Entry, Version
from src.versions.diff import diff_versions
from src.versions.snapshot import version_metrics_dict

FOCUS_SHIFT_DAYS = 90
WEEKLY_TREND_WEEKS = 6


def _relative_change(before: float, after: float) -> float | None:
    if before == 0:
        return None
    return (after - before) / before


def _fmt_pct(x: float) -> str:
    sign = "+" if x >= 0 else ""
    return f"{sign}{x * 100:.0f}%"


@dataclass
class DashboardSummary:
    greeting_name: str | None
    hero_headline: str
    hero_stats: list[str]
    current_version: dict | None
    focus_shift: list[dict]
    focus_shift_note: str | None
    weekly_evolution: list[dict]
    insight: dict | None
    recent_activity: list[dict]
    streak: dict
    evolis_score: dict | None
    onboarding_gate: bool  # true when there's too little data for the dashboard to say much yet

    def to_dict(self) -> dict:
        return {
            "greeting_name": self.greeting_name,
            "hero_headline": self.hero_headline,
            "hero_stats": self.hero_stats,
            "current_version": self.current_version,
            "focus_shift": self.focus_shift,
            "focus_shift_note": self.focus_shift_note,
            "weekly_evolution": self.weekly_evolution,
            "insight": self.insight,
            "recent_activity": self.recent_activity,
            "streak": self.streak,
            "evolis_score": self.evolis_score,
            "onboarding_gate": self.onboarding_gate,
        }


def _current_version_card(db: Session, user_id: str) -> dict | None:
    versions = db.query(Version).filter(Version.user_id == user_id).order_by(Version.period_start).all()
    if not versions:
        return None

    latest = versions[-1]
    metrics = version_metrics_dict(latest)
    topic_scores: dict = metrics.get("topic_scores") or {}
    top_topic = next(iter(topic_scores), None)

    strongest_growth = None
    if len(versions) >= 2:
        diff = diff_versions(version_metrics_dict(versions[-2]), metrics)
        if diff.topic_score_changes:
            topic, change = max(diff.topic_score_changes.items(), key=lambda kv: kv[1])
            if change > 0:
                strongest_growth = {"topic": topic, "change": round(change, 4)}

    return {
        "label": latest.label,
        "period_start": latest.period_start.date().isoformat(),
        "period_end": latest.period_end.date().isoformat(),
        "primary_focus": top_topic,
        "strongest_growth": strongest_growth,
        "completion_rate": metrics.get("completion_rate"),
        "deep_work_hours_per_day": metrics.get("deep_work_hours_per_day"),
        "has_previous_version": len(versions) >= 2,
        "previous_label": versions[-2].label if len(versions) >= 2 else None,
    }


def _focus_shift(db: Session, user_id: str, now: dt.datetime) -> tuple[list[dict], str | None]:
    start = now - dt.timedelta(days=FOCUS_SHIFT_DAYS)
    scores = topic_interest_scores(db, user_id, start, now)
    if not scores:
        return [], None

    top = list(scores.items())[:6]
    bars = [{"topic": topic, "score": round(score, 3)} for topic, score in top]

    # Compare against the previous 90-day window for the "grown +X% since"
    # note under the bars.
    prev_start = start - dt.timedelta(days=FOCUS_SHIFT_DAYS)
    prev_scores = topic_interest_scores(db, user_id, prev_start, start)

    note = None
    best_topic, best_change = None, 0.0
    for topic, score in top:
        change = _relative_change(prev_scores.get(topic, 0.0), score)
        if change is not None and change > best_change:
            best_topic, best_change = topic, change
    if best_topic:
        note = f"{best_topic} has grown {_fmt_pct(best_change)} since your previous 90 days."

    return bars, note


def weekly_behavior_deltas(db: Session, user_id: str, now: dt.datetime) -> list[dict]:
    this_start, this_end = period_bounds("weekly", now.date())
    last_start, last_end = period_bounds("weekly", (now - dt.timedelta(days=7)).date())

    this_week = behavior_summary(db, user_id, this_start, this_end)
    last_week = behavior_summary(db, user_id, last_start, last_end)

    def entry(key: str, label: str, higher_is_better: bool) -> dict:
        before, after = last_week.get(key, 0) or 0, this_week.get(key, 0) or 0
        change = _relative_change(before, after)
        # No change at all is neutral, not "bad" — (change >= 0) == higher_is_better
        # would otherwise call a flat context-switching week a regression.
        is_positive = None if not change else (change > 0) == higher_is_better
        return {"key": key, "label": label, "before": before, "after": after, "change": change, "is_positive": is_positive}

    return [
        entry("deep_work_hours_per_day", "Deep Work", higher_is_better=True),
        entry("completion_rate", "Completion", higher_is_better=True),
        entry("context_switching_per_day", "Context Switching", higher_is_better=False),
    ]


def _consecutive_growth_weeks(db: Session, user_id: str, topic: str, now: dt.datetime) -> int:
    """How many trailing weeks in a row this topic's interest score rose,
    the backbone of the "grown for N consecutive weeks" insight sentence."""
    weekly_scores: list[float] = []
    for i in range(WEEKLY_TREND_WEEKS):
        anchor = (now - dt.timedelta(weeks=i)).date()
        start, end = period_bounds("weekly", anchor)
        scores = topic_interest_scores(db, user_id, start, end)
        weekly_scores.append(scores.get(topic, 0.0))
    weekly_scores.reverse()  # oldest -> newest

    streak = 0
    for prev, curr in zip(weekly_scores, weekly_scores[1:]):
        if curr > prev:
            streak += 1
        else:
            streak = 0
    return streak


def _build_insight(db: Session, user_id: str, focus_bars: list[dict], now: dt.datetime) -> dict | None:
    anomalies = detect_learning_time_anomalies(db, user_id, now=now)
    if anomalies:
        a = anomalies[0]
        return {
            "type": "anomaly",
            "headline": f"{a.metric} is unusually high this week.",
            "detail": f"{round(a.current_value)} minutes vs your ~{round(a.baseline_mean)}-minute average.",
        }

    if focus_bars:
        top_topic = focus_bars[0]["topic"]
        weeks = _consecutive_growth_weeks(db, user_id, top_topic, now)
        if weeks >= 2:
            contributors = [b["topic"] for b in focus_bars[1:3]]
            detail = f"Most of that growth comes from {', '.join([top_topic] + contributors)}." if contributors else None
            return {
                "type": "growth_streak",
                "headline": f"Your {top_topic}-related activity has increased for {weeks} consecutive weeks.",
                "detail": detail,
            }

    pattern = detect_project_load_vs_completion(db, user_id, now=now)
    if pattern:
        return {"type": "pattern", "headline": pattern.description, "detail": None}

    if focus_bars:
        return {
            "type": "top_interest",
            "headline": f"{focus_bars[0]['topic']} is your strongest focus area right now.",
            "detail": None,
        }

    return None


def _recent_activity(db: Session, user_id: str, today: dt.date, limit: int = 5) -> list[dict]:
    entries = (
        db.query(Entry)
        .filter(Entry.user_id == user_id)
        .order_by(Entry.entry_date.desc())
        .limit(limit)
        .all()
    )
    out = []
    for e in entries:
        d = e.entry_date.date() if isinstance(e.entry_date, dt.datetime) else e.entry_date
        days_ago = (today - d).days
        if days_ago == 0:
            when = "Today"
        elif days_ago == 1:
            when = "Yesterday"
        else:
            when = f"{days_ago} days ago"
        topics = [t.topic for t in e.topics][:2]
        summary = ", ".join(topics) if topics else (e.raw_text[:60] + ("…" if len(e.raw_text) > 60 else ""))
        out.append({"when": when, "date": d.isoformat(), "summary": summary})
    return out


def build_dashboard_summary(db: Session, user_id: str, display_name: str | None, now: dt.datetime | None = None) -> DashboardSummary:
    now = now or dt.datetime.utcnow()
    today = now.date()

    entry_count = db.query(Entry).filter(Entry.user_id == user_id).count()
    onboarding_gate = entry_count < 3

    streak_info = compute_streak(db, user_id, today=today)
    focus_bars, focus_note = _focus_shift(db, user_id, now)
    weekly = weekly_behavior_deltas(db, user_id, now)
    version_card = _current_version_card(db, user_id)
    insight = None if onboarding_gate else _build_insight(db, user_id, focus_bars, now)
    recent = _recent_activity(db, user_id, today)
    evolis_score = None if onboarding_gate else compute_evolis_score(db, user_id, now).to_dict()

    hero_stats = []
    deep_work_row = next((w for w in weekly if w["key"] == "deep_work_hours_per_day"), None)
    if deep_work_row and deep_work_row["change"] is not None:
        hero_stats.append(f"{_fmt_pct(deep_work_row['change'])} focused work")

    emerging_count = sum(1 for b in focus_bars if b["score"] >= 0.15) if focus_bars else 0
    if emerging_count:
        hero_stats.append(f"{emerging_count} active focus area{'s' if emerging_count != 1 else ''}")

    anomaly_count = len(detect_learning_time_anomalies(db, user_id, now=now)) if not onboarding_gate else 0
    if anomaly_count:
        hero_stats.append(f"{anomaly_count} unusual activity pattern{'s' if anomaly_count != 1 else ''} detected")

    if onboarding_gate:
        headline = "Log a few more days and Evolis will start showing you real patterns."
    elif focus_bars:
        headline = f"Your focus is shifting toward {focus_bars[0]['topic']}."
    else:
        headline = "Keep logging — your focus trend will show up here soon."

    return DashboardSummary(
        greeting_name=display_name,
        hero_headline=headline,
        hero_stats=hero_stats,
        current_version=version_card,
        focus_shift=focus_bars,
        focus_shift_note=focus_note,
        weekly_evolution=weekly,
        insight=insight,
        recent_activity=recent,
        streak={"current": streak_info.current_streak, "longest": streak_info.longest_streak},
        evolis_score=evolis_score,
        onboarding_gate=onboarding_gate,
    )
