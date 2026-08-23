"""Regression guard for extraction accuracy (sections 37-38).

Runs the always-available HeuristicExtractor against the golden dataset on
every test run. If ANTHROPIC_API_KEY is set, also runs AnthropicExtractor —
skipped otherwise since it costs money and needs network access; CI runs
without a key, so this half only exercises locally / when explicitly asked.

Thresholds are set against the current heuristic implementation, not some
aspirational target — the point is catching a regression (a prompt or
regex change that quietly makes extraction worse), not grading the
extractor's ceiling.
"""
import os

import pytest

from src.evaluation.extraction_eval import evaluate_extractor
from src.extraction.llm_extractor import AnthropicExtractor, HeuristicExtractor

MIN_TOPIC_F1 = 0.85
MIN_DURATION_ACCURACY = 0.85
MIN_ACTIVITY_ACCURACY = 0.85
MIN_COMPLETION_ACCURACY = 0.85


def test_heuristic_extractor_meets_accuracy_floor():
    report = evaluate_extractor(HeuristicExtractor())
    summary = report.summary()

    assert summary["topic_f1"] >= MIN_TOPIC_F1, summary
    assert summary["duration_accuracy"] >= MIN_DURATION_ACCURACY, summary
    assert summary["activity_accuracy"] >= MIN_ACTIVITY_ACCURACY, summary
    assert summary["completion_accuracy"] >= MIN_COMPLETION_ACCURACY, summary


@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="requires a real Claude API key")
def test_anthropic_extractor_meets_accuracy_floor():
    report = evaluate_extractor(AnthropicExtractor())
    summary = report.summary()

    assert summary["topic_f1"] >= 0.8
    assert summary["completion_accuracy"] >= 0.8
