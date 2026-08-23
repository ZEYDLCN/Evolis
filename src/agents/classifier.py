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

# Only a leading \b, not a trailing one: Turkish is agglutinative (ilgi ->
# ilgim, değiş -> değiştim, karşılaştır -> karşılaştırdım), so anchoring the
# end of the word would miss every inflected form and only ever match the
# bare stem — which barely occurs in real questions. "vs"/"when" are short
# ambiguous tokens where a trailing boundary is worth keeping to avoid
# matching inside an unrelated word.
# Checked in order, first match wins — so put the more specific / less
# ambiguous triggers first. "proje" (project_analysis) is the generic case:
# it shows up inside behavior/comparison questions too (e.g. spec's own
# "Neden daha az proje bitiriyorum?", a behavior_pattern example), so it's
# deliberately last.
_PATTERNS: list[tuple[QueryClass, re.Pattern]] = [
    ("comparison", re.compile(r"\bvs\b|karşılaştır|fark|arasında", re.IGNORECASE)),
    ("timeline", re.compile(r"ne zaman|\bwhen\b|zaman çizelgesi|timeline", re.IGNORECASE)),
    ("skill_progress", re.compile(r"skill|beceri|ilerle|öğren", re.IGNORECASE)),
    ("behavior_pattern", re.compile(r"neden|niye|pattern|davranış|alışkanlık", re.IGNORECASE)),
    ("interest_change", re.compile(r"ilgi|interest|yönel|değiş", re.IGNORECASE)),
    ("project_analysis", re.compile(r"proje|project", re.IGNORECASE)),
]


def classify_query(question: str) -> QueryClass:
    for query_class, pattern in _PATTERNS:
        if pattern.search(question):
            return query_class
    return "search"
