import pytest

from src.evaluation.retrieval_eval import mean_reciprocal_rank, precision_at_k, recall_at_k, reciprocal_rank


def test_precision_and_recall_at_k():
    retrieved = ["a", "b", "c", "d"]
    relevant = {"b", "d", "e"}

    assert precision_at_k(retrieved, relevant, k=2) == 0.5  # b in top 2
    assert precision_at_k(retrieved, relevant, k=4) == 0.5  # b, d in top 4
    assert recall_at_k(retrieved, relevant, k=4) == pytest.approx(2 / 3)


def test_reciprocal_rank():
    assert reciprocal_rank(["a", "b", "c"], {"b"}) == 0.5
    assert reciprocal_rank(["a", "b", "c"], {"a"}) == 1.0
    assert reciprocal_rank(["a", "b", "c"], {"z"}) == 0.0


def test_mean_reciprocal_rank():
    all_retrieved = [["a", "b"], ["x", "y", "z"]]
    all_relevant = [{"b"}, {"z"}]
    assert mean_reciprocal_rank(all_retrieved, all_relevant) == pytest.approx((0.5 + 1 / 3) / 2)


def test_empty_inputs_dont_crash():
    assert precision_at_k([], {"a"}, k=5) == 0.0
    assert recall_at_k(["a"], set(), k=5) == 0.0
    assert mean_reciprocal_rank([], []) == 0.0
