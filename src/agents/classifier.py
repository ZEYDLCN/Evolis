"""Intent Classification — section 21/22.

Rule-based for the MVP (cheap, deterministic, easy to test). Swap for an
LLM-backed classifier later without touching the planner/analyst contracts.
"""
from __future__ import annotations

import re
from typing import Literal

QueryClass = Literal[
    "interest_change",
    "skill_progress",
    "project_analysis",
    "behavior_pattern",
    "timeline",
    "comparison",
    "search",
]

_PATTERNS: list[tuple[QueryClass, re.Pattern]] = [
    ("comparison", re.compile(r"\b(vs|karşılaştır|fark|arasında)\b", re.IGNORECASE)),
    ("skill_progress", re.compile(r"\b(skill|beceri|ilerle|öğren)\b", re.IGNORECASE)),
    ("project_analysis", re.compile(r"\b(proje|project)\b", re.IGNORECASE)),
    ("behavior_pattern", re.compile(r"\b(neden|niye|pattern|davranış|alışkanlık)\b", re.IGNORECASE)),
    ("timeline", re.compile(r"\b(ne zaman|when|zaman çizelgesi|timeline)\b", re.IGNORECASE)),
    ("interest_change", re.compile(r"\b(ilgi|interest|yön|değiş)\b", re.IGNORECASE)),
]


def classify_query(question: str) -> QueryClass:
    for query_class, pattern in _PATTERNS:
        if pattern.search(question):
            return query_class
    return "search"
