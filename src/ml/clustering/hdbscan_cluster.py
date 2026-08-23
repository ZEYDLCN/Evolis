"""Semantic topic discovery over entry embeddings.

HDBSCAN is the primary method (variable cluster count, marks noise points);
K-Means is kept as a baseline for comparison / evaluation. Both are optional
dependencies — callers should treat clustering as best-effort and handle the
`None` result (e.g. too few points, or scikit-learn/hdbscan not installed).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ClusterAssignment:
    labels: list[int]  # -1 == noise (HDBSCAN only)
    method: str


def cluster_embeddings(vectors: list[list[float]], min_cluster_size: int = 3) -> ClusterAssignment | None:
    if len(vectors) < min_cluster_size:
        return None

    try:
        import hdbscan
        import numpy as np

        clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric="euclidean")
        labels = clusterer.fit_predict(np.array(vectors))
        return ClusterAssignment(labels=labels.tolist(), method="hdbscan")
    except ImportError:
        return _kmeans_fallback(vectors, min_cluster_size)


def _kmeans_fallback(vectors: list[list[float]], min_cluster_size: int) -> ClusterAssignment | None:
    try:
        import numpy as np
        from sklearn.cluster import KMeans

        k = max(2, len(vectors) // max(min_cluster_size, 1))
        k = min(k, len(vectors))
        model = KMeans(n_clusters=k, n_init="auto", random_state=42)
        labels = model.fit_predict(np.array(vectors))
        return ClusterAssignment(labels=labels.tolist(), method="kmeans")
    except ImportError:
        return None
