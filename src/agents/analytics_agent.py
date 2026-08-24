"""Analyst step: runs the deterministic SQL/analytics tools the planner selected."""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.agents.planner import QueryPlan
from src.analytics.interests import topic_interest_scores
from src.analytics.productivity import behavior_summary
from src.analytics.skills import skill_scores
from src.database.models import Entry
from src.rag.retriever import RetrievedEntry, hybrid_search
from src.services.evolution_event_service import rank_decisions_by_impact


def run_analysis(db: Session, user_id: str, plan: QueryPlan, question: str) -> dict:
    result: dict = {"query_class": plan.query_class}

    # Always tracked, regardless of path — section 13's "Based on N entries"
    # grounding line needs a real count, not an estimate.
    result["entries_analyzed"] = (
        db.query(Entry).filter(Entry.user_id == user_id, Entry.entry_date >= plan.start, Entry.entry_date < plan.end).count()
    )

    if plan.use_sql:
        result["interests"] = topic_interest_scores(db, user_id, plan.start, plan.end)
        result["skills"] = skill_scores(db, user_id, plan.start, plan.end)
        result["behavior"] = behavior_summary(db, user_id, plan.start, plan.end)

    if plan.query_class == "decision_impact":
        # "Which decisions changed my direction the most?" — ranked by
        # magnitude of coincident change, never phrased as causal (see
        # src/services/evolution_event_service.py's module docstring).
        result["ranked_decisions"] = rank_decisions_by_impact(db, user_id)

    if plan.use_vector_search:
        hits: list[RetrievedEntry] = hybrid_search(db, user_id, question, top_k=5)
        result["retrieved_entries"] = [{"text": h.text, "score": h.score} for h in hits]

    return result
