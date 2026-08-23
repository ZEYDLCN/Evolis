"""Skill Evolution scoring — section 10.

Deliberately NOT an LLM estimate. Built from deterministic signals:
learning frequency, practice frequency, project usage, quiz/completion
events, and recency. Weights are tunable; defaults favor recent, applied
practice over passive learning.
"""
from __future__ import annotations

from dataclasses import dataclass

WEIGHTS = {
    "learning_frequency": 0.20,
    "practice_frequency": 0.20,
    "project_usage": 0.30,
    "completion_events": 0.20,
    "recency": 0.10,
}


@dataclass
class SkillSignal:
    learning_frequency: float  # normalized [0,1]
    practice_frequency: float
    project_usage: float
    completion_events: float
    recency: float


def compute_skill_score(signal: SkillSignal, scale: int = 100) -> int:
    raw = (
        WEIGHTS["learning_frequency"] * signal.learning_frequency
        + WEIGHTS["practice_frequency"] * signal.practice_frequency
        + WEIGHTS["project_usage"] * signal.project_usage
        + WEIGHTS["completion_events"] * signal.completion_events
        + WEIGHTS["recency"] * signal.recency
    )
    return round(max(0.0, min(1.0, raw)) * scale)
