"""Ask Evolis — end-to-end pipeline (section 21-22).

    Question -> Classifier -> Planner -> Analyst (SQL + vector search)
             -> LLM Explanation -> Verifier -> Answer

Actually orchestrated as a LangGraph StateGraph now (src/agents/graph.py);
ask() below is the stable public entry point the API router calls, kept
separate from the graph wiring so callers never depend on LangGraph
directly. _explain/_template_explain stay here since they're about wording
the answer, not about the graph's control flow.
"""
from __future__ import annotations

import os

from sqlalchemy.orm import Session

from src.monitoring.metrics import llm_calls_total

EXPLAIN_SYSTEM_PROMPT = """You are Evolis's analyst voice. You are given a
user's question and a JSON payload of pre-computed analytics (interest
scores, skill scores, behavior metrics, retrieved past entries). Answer the
question using ONLY numbers present in the payload — never invent a
percentage or count. Be concise, second person, and specific. Respond in the
same language as the question."""


def ask(db: Session, user_id: str, question: str) -> dict:
    from src.agents.graph import run_ask_graph

    return run_ask_graph(db, user_id, question)


def _explain(question: str, analysis: dict) -> str:
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            import anthropic

            client = anthropic.Anthropic()
            response = client.messages.create(
                model="claude-sonnet-5",
                max_tokens=512,
                system=EXPLAIN_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": f"Question: {question}\n\nData: {analysis}"}],
            )
            llm_calls_total.labels(purpose="ask_explain", outcome="success").inc()
            return "".join(b.text for b in response.content if b.type == "text")
        except Exception:
            llm_calls_total.labels(purpose="ask_explain", outcome="error").inc()

    llm_calls_total.labels(purpose="ask_explain", outcome="fallback").inc()
    return _template_explain(analysis)


def _template_explain(analysis: dict) -> str:
    parts = []
    if "interests" in analysis and analysis["interests"]:
        top = list(analysis["interests"].items())[:3]
        parts.append("Top interests: " + ", ".join(f"{t} ({s:.2f})" for t, s in top))
    if "behavior" in analysis:
        b = analysis["behavior"]
        parts.append(
            f"Completion rate {b['completion_rate']*100:.0f}%, "
            f"deep work {b['deep_work_hours_per_day']}h/day, "
            f"context switching {b['context_switching_per_day']}/day."
        )
    if "retrieved_entries" in analysis and analysis["retrieved_entries"]:
        parts.append(f"Found {len(analysis['retrieved_entries'])} related past entries.")
    return " ".join(parts) or "Not enough data yet to answer this."
