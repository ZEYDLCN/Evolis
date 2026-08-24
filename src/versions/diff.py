"""Diff Engine — the core product feature (sections 4, 27).

Pure function over two version-metrics dicts (see snapshot.version_metrics_dict).
No LLM involved: every number here is computed, not generated. An LLM may be
layered on top (see src/agents) purely to phrase the numbers as prose for
"Release Notes For You".
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.extraction.domains import DOMAIN_LABELS, classify_domain

NEW_TOPIC_THRESHOLD = 0.15  # below this in the base version, above it in the target -> "added"
DECLINE_THRESHOLD = -0.20  # relative change below this -> "declining"
IMPROVE_THRESHOLD = 0.10
DORMANT_THRESHOLD = 0.05  # topic present in base, drops below this in target -> "dormant"


@dataclass
class VersionDiff:
    added_topics: list[str] = field(default_factory=list)
    declining_topics: list[str] = field(default_factory=list)
    dormant_topics: list[str] = field(default_factory=list)
    emerging_topics: list[str] = field(default_factory=list)
    topic_score_changes: dict[str, float] = field(default_factory=dict)
    skill_changes: dict[str, dict] = field(default_factory=dict)
    completion_change: float | None = None
    deep_work_change: float | None = None
    context_switching_change: float | None = None
    # Raw before/after values, for a UI that wants to show "2.2h -> 3.1h"
    # rather than just "+41%" (section 9's Interactive Diff mockup).
    completion_before: float | None = None
    completion_after: float | None = None
    deep_work_before: float | None = None
    deep_work_after: float | None = None
    context_switching_before: float | None = None
    context_switching_after: float | None = None
    # Broader life tracking (not just tech): every topic name mentioned
    # anywhere in this diff, labeled with its life domain — Skills, Work &
    # Projects, Learning, Habits & Routines, Personal Growth, or Behavior
    # — so a UI can group "New/Improved/Declining" the way a real Evolis
    # version diff should read, not as one flat topic list.
    topic_domains: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "added_topics": self.added_topics,
            "declining_topics": self.declining_topics,
            "dormant_topics": self.dormant_topics,
            "emerging_topics": self.emerging_topics,
            "topic_score_changes": self.topic_score_changes,
            "skill_changes": self.skill_changes,
            "completion_change": self.completion_change,
            "deep_work_change": self.deep_work_change,
            "context_switching_change": self.context_switching_change,
            "completion_before": self.completion_before,
            "completion_after": self.completion_after,
            "deep_work_before": self.deep_work_before,
            "deep_work_after": self.deep_work_after,
            "context_switching_before": self.context_switching_before,
            "context_switching_after": self.context_switching_after,
            "topic_domains": self.topic_domains,
        }


def _relative_change(before: float, after: float) -> float:
    if before == 0:
        return float("inf") if after > 0 else 0.0
    return (after - before) / before


def diff_versions(base_metrics: dict, target_metrics: dict) -> VersionDiff:
    base_topics: dict = base_metrics.get("topic_scores", {}) or {}
    target_topics: dict = target_metrics.get("topic_scores", {}) or {}

    diff = VersionDiff()
    all_topics = set(base_topics) | set(target_topics)

    for topic in all_topics:
        before = base_topics.get(topic, 0.0)
        after = target_topics.get(topic, 0.0)
        diff.topic_score_changes[topic] = round(after - before, 4)
        diff.topic_domains[topic] = DOMAIN_LABELS[classify_domain(topic)]

        if topic not in base_topics and after >= NEW_TOPIC_THRESHOLD:
            diff.added_topics.append(topic)
        elif before < NEW_TOPIC_THRESHOLD and after >= NEW_TOPIC_THRESHOLD:
            diff.emerging_topics.append(topic)
        elif topic in base_topics and after <= DORMANT_THRESHOLD and before > DORMANT_THRESHOLD:
            diff.dormant_topics.append(topic)
        elif before > 0:
            change = _relative_change(before, after)
            if change <= DECLINE_THRESHOLD:
                diff.declining_topics.append(topic)

    base_skills = {s["skill"]: s for s in (base_metrics.get("skill_scores") or [])}
    target_skills = {s["skill"]: s for s in (target_metrics.get("skill_scores") or [])}
    for skill, target_data in target_skills.items():
        before_score = base_skills.get(skill, {}).get("activity_score", 0)
        diff.skill_changes[skill] = {
            "before": before_score,
            "after": target_data["activity_score"],
            "change": target_data["activity_score"] - before_score,
        }

    if "completion_rate" in base_metrics and "completion_rate" in target_metrics:
        diff.completion_before = base_metrics["completion_rate"]
        diff.completion_after = target_metrics["completion_rate"]
        diff.completion_change = round(target_metrics["completion_rate"] - base_metrics["completion_rate"], 4)
    if "deep_work_hours_per_day" in base_metrics and "deep_work_hours_per_day" in target_metrics:
        diff.deep_work_before = base_metrics["deep_work_hours_per_day"]
        diff.deep_work_after = target_metrics["deep_work_hours_per_day"]
        diff.deep_work_change = round(
            _relative_change(base_metrics["deep_work_hours_per_day"], target_metrics["deep_work_hours_per_day"]), 4
        )
    if "context_switching_per_day" in base_metrics and "context_switching_per_day" in target_metrics:
        diff.context_switching_before = base_metrics["context_switching_per_day"]
        diff.context_switching_after = target_metrics["context_switching_per_day"]
        diff.context_switching_change = round(
            target_metrics["context_switching_per_day"] - base_metrics["context_switching_per_day"], 4
        )

    return diff
