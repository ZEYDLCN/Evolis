"""Automatic Topic Naming — section 9.

The LLM only ever sees a handful of representative entries per cluster
(never the whole cluster), and its only job is to produce a short label.
Falls back to a deterministic label (most frequent topic string in the
cluster) when no LLM is configured, so cluster persistence still works
offline.
"""
from __future__ import annotations

from src.llm.provider import active_provider, complete
from src.monitoring.metrics import llm_calls_total

SYSTEM_PROMPT = """You name a cluster of semantically related personal
activity-log entries with a short (2-4 word) topic label, e.g.
"RAG & Semantic Retrieval" or "Backend Infrastructure". Respond with the
label only, no punctuation at the end, no quotes."""


def name_cluster(representative_texts: list[str], fallback_topics: list[str]) -> str:
    if active_provider():
        try:
            label = complete(SYSTEM_PROMPT, "\n".join(representative_texts[:5]), max_tokens=32).strip()
            if label:
                llm_calls_total.labels(purpose="cluster_naming", outcome="success").inc()
                return label
        except Exception:
            llm_calls_total.labels(purpose="cluster_naming", outcome="error").inc()

    llm_calls_total.labels(purpose="cluster_naming", outcome="fallback").inc()
    return _fallback_label(fallback_topics)


def _fallback_label(topics: list[str]) -> str:
    if not topics:
        return "Uncategorized"
    seen: list[str] = []
    for t in topics:
        if t not in seen:
            seen.append(t)
    return " & ".join(seen[:3])
