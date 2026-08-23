"""Query Planner — decides which tools the analyst needs and extracts a time range.

Time-range extraction is intentionally simple (last N months / "this year" /
default lookback) rather than a full NL date parser; good enough for the Ask
LifeDiff MVP and easy to extend.
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass

from src.agents.classifier import QueryClass

_MONTHS_RE = re.compile(r"(\d+)\s*(ay|month)", re.IGNORECASE)


@dataclass
class QueryPlan:
    query_class: QueryClass
    start: dt.datetime
    end: dt.datetime
    use_sql: bool
    use_vector_search: bool


def build_plan(question: str, query_class: QueryClass, now: dt.datetime | None = None) -> QueryPlan:
    now = now or dt.datetime.utcnow()
    months_back = 6
    match = _MONTHS_RE.search(question)
    if match:
        months_back = int(match.group(1))

    start = now - dt.timedelta(days=30 * months_back)

    use_sql = query_class in {"interest_change", "skill_progress", "project_analysis", "behavior_pattern", "comparison", "timeline"}
    use_vector_search = query_class in {"search", "behavior_pattern", "comparison"}

    return QueryPlan(query_class=query_class, start=start, end=now, use_sql=use_sql, use_vector_search=use_vector_search)
