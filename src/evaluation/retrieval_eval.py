"""Retrieval evaluation — section 37: Precision@K, Recall@K, MRR.

Generic over any ranked list of ids, so it works the same whether the
ranking came from src.rag.retriever.hybrid_search, vector_search alone, or
a future reranker — no DB dependency here, just set math over ids.
"""
from __future__ import annotations


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for rid in top_k if rid in relevant_ids)
    return hits / len(top_k)


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    hits = sum(1 for rid in top_k if rid in relevant_ids)
    return hits / len(relevant_ids)


def reciprocal_rank(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    for rank, rid in enumerate(retrieved_ids, start=1):
        if rid in relevant_ids:
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(all_retrieved: list[list[str]], all_relevant: list[set[str]]) -> float:
    scores = [reciprocal_rank(retrieved, relevant) for retrieved, relevant in zip(all_retrieved, all_relevant)]
    return sum(scores) / len(scores) if scores else 0.0
