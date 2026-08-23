"""Extraction accuracy evaluation — sections 37-38.

Runs any Extractor against the golden dataset
(tests/evaluation/golden_dataset.json) and scores it on the four things that
matter for the pipeline: topic extraction (precision/recall/F1, case- and
whitespace-insensitive set comparison), duration extraction (exact-match
rate), activity-type classification, and completion-status classification.

This is a regression harness, not a benchmark of "how good is the LLM at
this" — the point is to catch a prompt or fallback-heuristic change that
quietly makes extraction worse, by running it against the same golden
dataset before and after and diffing the scores.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.extraction.llm_extractor import Extractor
from src.extraction.schemas import ExtractedEntry

DEFAULT_DATASET_PATH = Path(__file__).resolve().parent.parent.parent / "tests" / "evaluation" / "golden_dataset.json"


@dataclass
class GoldenExample:
    input: str
    expected_topics: list[str]
    expected_duration_minutes: int | None
    expected_activity: str | None
    expected_completion_status: str | None


@dataclass
class ExampleResult:
    example: GoldenExample
    predicted: ExtractedEntry
    topic_precision: float
    topic_recall: float
    duration_correct: bool
    activity_correct: bool
    completion_correct: bool


@dataclass
class EvalReport:
    results: list[ExampleResult] = field(default_factory=list)

    @property
    def topic_precision(self) -> float:
        return _mean(r.topic_precision for r in self.results)

    @property
    def topic_recall(self) -> float:
        return _mean(r.topic_recall for r in self.results)

    @property
    def topic_f1(self) -> float:
        p, r = self.topic_precision, self.topic_recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    @property
    def duration_accuracy(self) -> float:
        return _mean(1.0 if r.duration_correct else 0.0 for r in self.results)

    @property
    def activity_accuracy(self) -> float:
        return _mean(1.0 if r.activity_correct else 0.0 for r in self.results)

    @property
    def completion_accuracy(self) -> float:
        return _mean(1.0 if r.completion_correct else 0.0 for r in self.results)

    def summary(self) -> dict:
        return {
            "n_examples": len(self.results),
            "topic_precision": round(self.topic_precision, 3),
            "topic_recall": round(self.topic_recall, 3),
            "topic_f1": round(self.topic_f1, 3),
            "duration_accuracy": round(self.duration_accuracy, 3),
            "activity_accuracy": round(self.activity_accuracy, 3),
            "completion_accuracy": round(self.completion_accuracy, 3),
        }


def _mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _normalize(topic: str) -> str:
    return " ".join(topic.lower().split())


def load_golden_dataset(path: Path = DEFAULT_DATASET_PATH) -> list[GoldenExample]:
    raw = json.loads(path.read_text())
    return [
        GoldenExample(
            input=row["input"],
            expected_topics=row["expected_topics"],
            expected_duration_minutes=row.get("expected_duration_minutes"),
            expected_activity=row.get("expected_activity"),
            expected_completion_status=row.get("expected_completion_status"),
        )
        for row in raw
    ]


def _score_topics(expected: list[str], predicted: list[str]) -> tuple[float, float]:
    expected_set = {_normalize(t) for t in expected}
    predicted_set = {_normalize(t) for t in predicted}

    if not expected_set and not predicted_set:
        return 1.0, 1.0
    if not predicted_set:
        return 1.0, 0.0  # nothing predicted -> vacuously precise, but recalls nothing
    if not expected_set:
        return 0.0, 1.0  # predicted something where nothing was expected -> imprecise

    true_positives = len(expected_set & predicted_set)
    precision = true_positives / len(predicted_set)
    recall = true_positives / len(expected_set)
    return precision, recall


def evaluate_extractor(extractor: Extractor, dataset: list[GoldenExample] | None = None) -> EvalReport:
    dataset = dataset if dataset is not None else load_golden_dataset()
    report = EvalReport()

    for example in dataset:
        predicted = extractor.extract(example.input)
        precision, recall = _score_topics(example.expected_topics, predicted.topics)

        predicted_duration = predicted.activities[0].duration_minutes if predicted.activities else None
        duration_correct = predicted_duration == example.expected_duration_minutes

        if example.expected_activity is None:
            activity_correct = len(predicted.activities) == 0
        else:
            activity_correct = any(a.type == example.expected_activity for a in predicted.activities)

        completion_correct = predicted.completion_status == example.expected_completion_status

        report.results.append(
            ExampleResult(
                example=example,
                predicted=predicted,
                topic_precision=precision,
                topic_recall=recall,
                duration_correct=duration_correct,
                activity_correct=activity_correct,
                completion_correct=completion_correct,
            )
        )

    return report
