"""Shared time-bucketing helpers for weekly/monthly/quarterly aggregation."""
from __future__ import annotations

import datetime as dt
from typing import Literal

Period = Literal["daily", "weekly", "monthly", "quarterly"]


def period_bounds(period: Period, anchor: dt.date | None = None) -> tuple[dt.datetime, dt.datetime]:
    """Returns [start, end) datetimes for the bucket containing `anchor`."""
    anchor = anchor or dt.date.today()

    if period == "daily":
        start = dt.datetime.combine(anchor, dt.time.min)
        return start, start + dt.timedelta(days=1)

    if period == "weekly":
        start_date = anchor - dt.timedelta(days=anchor.weekday())
        start = dt.datetime.combine(start_date, dt.time.min)
        return start, start + dt.timedelta(days=7)

    if period == "monthly":
        start = dt.datetime(anchor.year, anchor.month, 1)
        if anchor.month == 12:
            end = dt.datetime(anchor.year + 1, 1, 1)
        else:
            end = dt.datetime(anchor.year, anchor.month + 1, 1)
        return start, end

    # quarterly
    quarter = (anchor.month - 1) // 3
    start_month = quarter * 3 + 1
    start = dt.datetime(anchor.year, start_month, 1)
    end_month = start_month + 3
    if end_month > 12:
        end = dt.datetime(anchor.year + 1, end_month - 12, 1)
    else:
        end = dt.datetime(anchor.year, end_month, 1)
    return start, end


def daterange_buckets(start: dt.date, end: dt.date, period: Period) -> list[tuple[dt.datetime, dt.datetime]]:
    """List of consecutive [start, end) buckets covering [start, end]."""
    buckets = []
    cursor = start
    while cursor <= end:
        bucket_start, bucket_end = period_bounds(period, cursor)
        buckets.append((bucket_start, bucket_end))
        cursor = bucket_end.date()
    return buckets
