"""Skill Graph — section 11.

Node metrics (activity_score, first_seen, last_seen, project_usage,
learning_sessions) are fully computed, per the LLM != Analytics Engine rule
— see src/analytics/skills.py. Edges represent a *curated* prerequisite/
progression map (this is domain knowledge, not something to infer
statistically from one user's data), and only the edges where both
endpoints exist in the user's own skill data are ever returned — the graph
always reflects what this specific user has actually engaged with.

The curated map is intentionally small and meant to grow; add entries as
new domains matter (e.g. a frontend or data-eng track next to the AI one
below).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

import datetime as dt

from src.analytics.skills import skill_scores

# (prerequisite -> skill) edges. Case-insensitive match against extracted
# topic/skill names.
SKILL_PROGRESSION: list[tuple[str, str]] = [
    ("Python", "Machine Learning"),
    ("Machine Learning", "Deep Learning"),
    ("Deep Learning", "Transformer"),
    ("Transformer", "Embeddings"),
    ("Embeddings", "RAG"),
    ("RAG", "Agentic AI"),
    ("Python", "Backend Architecture"),
    ("Backend Architecture", "FastAPI"),
    ("FastAPI", "Docker"),
    ("RAG", "LangGraph"),
    ("LangGraph", "Agentic AI"),
]


def build_skill_graph(db: Session, user_id: str, start: dt.datetime, end: dt.datetime) -> dict:
    nodes = {n["skill"].lower(): n for n in skill_scores(db, user_id, start, end)}

    edges = [
        {"from": a, "to": b}
        for a, b in SKILL_PROGRESSION
        if a.lower() in nodes and b.lower() in nodes
    ]

    return {
        "nodes": [
            {
                "skill": n["skill"],
                "activity_score": n["activity_score"],
                "first_seen": n["first_seen"],
                "last_seen": n["last_seen"],
                "project_usage": n["project_usage"],
                "learning_sessions": n["learning_sessions"],
            }
            for n in nodes.values()
        ],
        "edges": edges,
    }
