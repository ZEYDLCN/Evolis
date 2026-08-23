"""Interest Score — section 5.

Interest Score =
    0.30 * normalized_mentions
  + 0.25 * normalized_duration
  + 0.20 * recency_score
  + 0.15 * project_usage
  + 0.10 * learning_frequency

All inputs are pre-normalized to [0, 1] by the caller (this module owns the
weighting formula and the recency decay, not the raw aggregation queries —
those live in src/analytics/interests.py).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

WEIGHTS = {
    "mentions": 0.30,
    "duration": 0.25,
    "recency": 0.20,
    "project_usage": 0.15,
    "learning_frequency": 0.10,
}


@dataclass
class InterestSignal:
    normalized_mentions: float
    normalized_duration: float
    recency_score: float
    project_usage: float
    learning_frequency: float


def compute_interest_score(signal: InterestSignal) -> float:
    score = (
        WEIGHTS["mentions"] * signal.normalized_mentions
        + WEIGHTS["duration"] * signal.normalized_duration
        + WEIGHTS["recency"] * signal.recency_score
        + WEIGHTS["project_usage"] * signal.project_usage
        + WEIGHTS["learning_frequency"] * signal.learning_frequency
    )
    return max(0.0, min(1.0, score))


def recency_score(days_since_last_mention: int, half_life_days: float = 21.0) -> float:
    """Exponential decay: score halves every `half_life_days`."""
    return math.exp(-math.log(2) * days_since_last_mention / half_life_days)


def normalize(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0.0
    return max(0.0, min(1.0, value / max_value))
