"""Ask Evolis as an actual LangGraph StateGraph — section 22.

Same five stages as the original plain-function pipeline
(src/agents/orchestrator.py), now wired as graph nodes:

    classify -> plan -> analyze -> explain -> verify -> END

Kept as a thin wrapper rather than a rewrite: classify_query, build_plan,
run_analysis, and verify_grounded are unchanged, pure functions reused
as-is; _explain/_template_explain stay in orchestrator.py so there's one
place that owns "how the answer gets worded." The graph is compiled once
and cached — compiling on every request would be pure overhead for a
five-node linear graph with no branching or cycles.
"""
from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from src.agents.classifier import QueryClass, classify_query
from src.agents.planner import QueryPlan, build_plan
from src.agents.analytics_agent import run_analysis
from src.agents.verifier import verify_grounded


class AskState(TypedDict, total=False):
    db: Session
    user_id: str
    question: str
    query_class: QueryClass
    plan: QueryPlan
    analysis: dict
    answer: str
    grounded: bool


def _classify_node(state: AskState) -> dict:
    return {"query_class": classify_query(state["question"])}


def _plan_node(state: AskState) -> dict:
    return {"plan": build_plan(state["question"], state["query_class"])}


def _analyze_node(state: AskState) -> dict:
    analysis = run_analysis(state["db"], state["user_id"], state["plan"], state["question"])
    return {"analysis": analysis}


def _explain_node(state: AskState) -> dict:
    # Imported lazily to avoid a module-import cycle: orchestrator.ask()
    # calls into this graph, and this graph calls back into
    # orchestrator's wording functions.
    from src.agents.orchestrator import _explain

    return {"answer": _explain(state["question"], state["analysis"])}


def _verify_node(state: AskState) -> dict:
    from src.agents.orchestrator import _template_explain

    if verify_grounded(state["answer"], state["analysis"]):
        return {"grounded": True}
    # Ungrounded — fall back to the deterministic, always-grounded template
    # rather than surfacing a number the LLM made up.
    return {"answer": _template_explain(state["analysis"]), "grounded": True}


def _build_graph() -> Any:
    graph = StateGraph(AskState)
    graph.add_node("classify", _classify_node)
    graph.add_node("plan", _plan_node)
    graph.add_node("analyze", _analyze_node)
    graph.add_node("explain", _explain_node)
    graph.add_node("verify", _verify_node)

    graph.set_entry_point("classify")
    graph.add_edge("classify", "plan")
    graph.add_edge("plan", "analyze")
    graph.add_edge("analyze", "explain")
    graph.add_edge("explain", "verify")
    graph.add_edge("verify", END)

    return graph.compile()


_compiled = None


def get_compiled_graph() -> Any:
    global _compiled
    if _compiled is None:
        _compiled = _build_graph()
    return _compiled


def run_ask_graph(db: Session, user_id: str, question: str) -> dict:
    result = get_compiled_graph().invoke({"db": db, "user_id": user_id, "question": question})
    return {
        "question": question,
        "query_class": result["query_class"],
        "analysis": result["analysis"],
        "answer": result["answer"],
        "grounded": result.get("grounded", True),
    }
