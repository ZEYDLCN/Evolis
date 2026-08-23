"""Analyst step: runs the deterministic SQL/analytics tools the planner selected."""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.agents.planner import QueryPlan
from src.analytics.interests import topic_interest_scores
from src.analytics.productivity import behavior_summary
from src.analytics.skills import skill_scores
from src.rag.retriever import RetrievedEntry, hybrid_search


def run_analysis(db: Session, user_id: str, plan: QueryPlan, question: str) -> dict:
    result: dict = {"query_class": plan.query_class}

    if plan.use_sql:
        result["interests"] = topic_interest_scores(db, user_id, plan.start, plan.end)
        result["skills"] = skill_scores(db, user_id, plan.start, plan.end)
        result["behavior"] = behavior_summary(db, user_id, plan.start, plan.end)

    if plan.use_vector_search:
        hits: list[RetrievedEntry] = hybrid_search(db, user_id, question, top_k=5)
        result["retrieved_entries"] = [{"text": h.text, "score": h.score} for h in hits]

    return result
