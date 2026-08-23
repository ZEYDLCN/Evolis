"""Ask LifeDiff — end-to-end pipeline (section 21-22).

    Question -> Classifier -> Planner -> Analyst (SQL + vector search)
             -> LLM Explanation -> Verifier -> Answer

This is a plain function pipeline today; the shape mirrors what a LangGraph
StateGraph would look like (each stage is a pure function over/into a shared
state dict) so migrating to LangGraph later is a mechanical refactor, not a
redesign.
"""
from __future__ import annotations

import os

from sqlalchemy.orm import Session

from src.agents.analytics_agent import run_analysis
from src.agents.classifier import classify_query
from src.agents.planner import build_plan
from src.agents.verifier import verify_grounded

EXPLAIN_SYSTEM_PROMPT = """You are LifeDiff's analyst voice. You are given a
user's question and a JSON payload of pre-computed analytics (interest
scores, skill scores, behavior metrics, retrieved past entries). Answer the
question using ONLY numbers present in the payload — never invent a
percentage or count. Be concise, second person, and specific. Respond in the
same language as the question."""


def ask(db: Session, user_id: str, question: str) -> dict:
    query_class = classify_query(question)
    plan = build_plan(question, query_class)
    analysis = run_analysis(db, user_id, plan, question)

    answer = _explain(question, analysis)
    grounded = verify_grounded(answer, analysis)
    if not grounded:
        answer = _template_explain(analysis)  # deterministic fallback, always grounded

    return {
        "question": question,
        "query_class": query_class,
        "analysis": analysis,
        "answer": answer,
        "grounded": True,
    }


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
            return "".join(b.text for b in response.content if b.type == "text")
        except Exception:
            pass
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
