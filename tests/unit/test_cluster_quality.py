import pytest

from src.ml.clustering.quality import silhouette, stability


def test_silhouette_none_with_single_cluster():
    vectors = [[0.0, 0.0], [0.1, 0.1], [0.2, 0.2]]
    labels = [0, 0, 0]
    assert silhouette(vectors, labels) is None


def test_silhouette_none_with_too_few_points():
    assert silhouette([[0.0]], [0]) is None


def test_stability_none_with_mismatched_lengths():
    assert stability([0, 1], [0, 1, 2]) is None


def test_stability_none_when_empty():
    assert stability([], []) is None


sklearn = pytest.importorskip("sklearn", reason="scikit-learn not installed; silhouette/stability fall back to None")


def test_silhouette_scores_well_separated_clusters_highly():
    vectors = [[0.0, 0.0], [0.1, 0.1], [10.0, 10.0], [10.1, 10.1]]
    labels = [0, 0, 1, 1]
    score = silhouette(vectors, labels)
    assert score is not None
    assert score > 0.9


def test_stability_identical_labelings_is_one():
    assert stability(["a", "a", "b"], ["a", "a", "b"]) == 1.0


def test_stability_random_relabeling_is_low():
    score = stability(["a", "b", "a", "b", "a", "b"], ["x", "x", "y", "y", "x", "y"])
    assert score is not None
    assert score < 0.5
