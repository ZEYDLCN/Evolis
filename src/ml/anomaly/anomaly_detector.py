"""Behavioral anomaly detection (section "Anomaly Detection").

Rolling mean + z-score is the primary, always-available method. Isolation
Forest is offered as a richer alternative when scikit-learn is installed and
enough history exists.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass


@dataclass
class Anomaly:
    metric: str
    current_value: float
    baseline_mean: float
    z_score: float

    @property
    def ratio(self) -> float:
        return self.current_value / self.baseline_mean if self.baseline_mean else float("inf")


def detect_zscore_anomaly(metric: str, current_value: float, history: list[float], threshold: float = 2.5) -> Anomaly | None:
    """history = same metric for prior comparable periods (e.g. last 8 weeks)."""
    if len(history) < 3:
        return None
    mean = statistics.fmean(history)
    stdev = statistics.pstdev(history) or 1e-9
    z = (current_value - mean) / stdev
    if abs(z) >= threshold:
        return Anomaly(metric=metric, current_value=current_value, baseline_mean=mean, z_score=z)
    return None


def detect_isolation_forest(samples: list[list[float]]) -> list[bool]:
    """Returns a per-sample is_anomaly flag. Falls back to all-False if
    scikit-learn isn't installed or there isn't enough data to fit."""
    if len(samples) < 10:
        return [False] * len(samples)
    try:
        from sklearn.ensemble import IsolationForest

        model = IsolationForest(random_state=42, contamination="auto")
        preds = model.fit_predict(samples)
        return [p == -1 for p in preds]
    except ImportError:
        return [False] * len(samples)
