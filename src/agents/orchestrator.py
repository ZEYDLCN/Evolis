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
same language as the question. If the payload includes "ranked_decisions",
describe them as changes that coincide with or were observed after the
decision — never claim the decision caused the change, and never speculate
about what would have happened had a different alternative been chosen."""


def ask(db: Session, user_id: str, question: str, lang: str = "en") -> dict:
    from src.agents.graph import run_ask_graph

    return run_ask_graph(db, user_id, question, lang)


def _explain(question: str, analysis: dict, lang: str = "en") -> str:
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            import anthropic

            client = anthropic.Anthropic()
            # The prompt already says "same language as the question" —
            # that's usually right (a Turkish entry gets a Turkish
            # answer). This only steers the rare case where the question
            # itself doesn't clearly signal a language.
            system = EXPLAIN_SYSTEM_PROMPT + (
                f"\n\nIf the question's language is ambiguous, default to {'Turkish' if lang == 'tr' else 'English'}."
            )
            response = client.messages.create(
                model="claude-sonnet-5",
                max_tokens=512,
                system=system,
                messages=[{"role": "user", "content": f"Question: {question}\n\nData: {analysis}"}],
            )
            llm_calls_total.labels(purpose="ask_explain", outcome="success").inc()
            return "".join(b.text for b in response.content if b.type == "text")
        except Exception:
            llm_calls_total.labels(purpose="ask_explain", outcome="error").inc()

    llm_calls_total.labels(purpose="ask_explain", outcome="fallback").inc()
    return _template_explain(analysis, lang)


def _template_explain(analysis: dict, lang: str = "en") -> str:
    parts = []
    if "ranked_decisions" in analysis:
        return _explain_ranked_decisions(analysis["ranked_decisions"], lang)

    if lang == "tr":
        if "interests" in analysis and analysis["interests"]:
            top = list(analysis["interests"].items())[:3]
            parts.append("En çok ilgi: " + ", ".join(f"{t} ({s:.2f})" for t, s in top))
        if "behavior" in analysis:
            b = analysis["behavior"]
            parts.append(
                f"Tamamlanma oranı %{b['completion_rate']*100:.0f}, "
                f"derin çalışma günde {b['deep_work_hours_per_day']} saat, "
                f"bağlam değişimi günde {b['context_switching_per_day']}."
            )
        if "retrieved_entries" in analysis and analysis["retrieved_entries"]:
            parts.append(f"{len(analysis['retrieved_entries'])} ilgili geçmiş kayıt bulundu.")
        return " ".join(parts) or "Bunu cevaplamak için henüz yeterli veri yok."

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


def _explain_ranked_decisions(ranked: list[dict], lang: str) -> str:
    """"Which decisions changed my direction the most?" — always phrased as
    coincidence/correlation ("coincide with"), never causation ("caused").
    See src/services/evolution_event_service.py for the no-causal-claims
    and no-fabricated-counterfactual rules this must keep honoring."""
    if not ranked:
        return (
            "Henüz yeterli sonrası-verisi olan bir karar yok, bu yüzden dönüm noktalarını sıralayamıyorum."
            if lang == "tr"
            else "No decisions have enough after-the-fact data yet to rank."
        )

    lines = []
    for i, r in enumerate(ranked, 1):
        title = r["event"]["title"]
        top_change = r.get("top_change")
        if top_change:
            topic, change = top_change["topic"], top_change["change"]
            sign = "+" if change >= 0 else ""
            detail = (
                f"{topic} ilgisinde {sign}{round(change * 100)} puan değişim gözlendi"
                if lang == "tr"
                else f"{topic} interest shifted {sign}{round(change * 100)} pts"
            )
        else:
            detail = "genel davranışta gözlenen değişim" if lang == "tr" else "an observed shift in overall behavior"
        lines.append(f"{i}. {title} → {detail}")

    header = (
        f"{len(ranked)} karar, gözlenen en büyük davranışsal değişimlerle örtüşüyor (bu bir nedensellik iddiası değildir):"
        if lang == "tr"
        else f"{len(ranked)} decision(s) coincide with your largest observed shifts (this isn't a causal claim):"
    )
    return header + " " + " ".join(lines)
