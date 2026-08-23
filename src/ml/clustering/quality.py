"""Clustering quality metrics — section 37 ("Clustering: Silhouette Score,
Cluster Stability, Human Evaluation").

Both metrics are optional/best-effort: silhouette needs scikit-learn and at
least 2 non-noise clusters; stability needs a previous labeling to compare
against. Both return None rather than raising when they can't be computed,
so callers can surface "not enough data yet" instead of a 500.
"""
from __future__ import annotations


def silhouette(vectors: list[list[float]], labels: list[int]) -> float | None:
    """Mean silhouette coefficient over non-noise (label != -1) points.

    Ranges roughly [-1, 1]; higher means clusters are dense and well
    separated. HDBSCAN's noise points (-1) are excluded since silhouette
    isn't meaningful for "not in any cluster".
    """
    try:
        from sklearn.metrics import silhouette_score
    except ImportError:
        return None

    kept = [(v, l) for v, l in zip(vectors, labels) if l != -1]
    if len(kept) < 2:
        return None

    kept_vectors = [v for v, _ in kept]
    kept_labels = [l for _, l in kept]
    if len(set(kept_labels)) < 2:
        return None  # silhouette is undefined for a single cluster

    return round(float(silhouette_score(kept_vectors, kept_labels)), 4)


def stability(previous_labels: list[int], current_labels: list[int]) -> float | None:
    """Adjusted Rand Index between two labelings of the *same* ordered
    points (e.g. this rebuild vs the last one), measuring how much cluster
    membership actually changed. 1.0 = identical, ~0 = no better than
    random relabeling.
    """
    try:
        from sklearn.metrics import adjusted_rand_score
    except ImportError:
        return None

    if len(previous_labels) != len(current_labels) or not previous_labels:
        return None

    return round(float(adjusted_rand_score(previous_labels, current_labels)), 4)
