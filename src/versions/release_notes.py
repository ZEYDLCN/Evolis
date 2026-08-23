"""Release Notes For You — section 28.

Pure formatting over an already-computed VersionDiff: no LLM, no new
numbers, just the changelog-style rendering the product spec shows as the
shareable card. (An actual image/card renderer is a frontend concern —
this returns the structured text a client renders however it likes.)
"""
from __future__ import annotations

from src.versions.diff import VersionDiff

KNOWN_ISSUE_MAX_PROJECTS = 4  # active projects touched in the target period considered a "Known Issue"


def render_release_notes(base_label: str, target_label: str, diff: VersionDiff, active_project_count: int | None = None) -> dict:
    lines = [f"YOU v{base_label} → YOU v{target_label}", ""]

    if diff.added_topics:
        lines.append("Added")
        lines += [f"+ {t}" for t in diff.added_topics]
        lines.append("")

    improved = []
    if diff.completion_change and diff.completion_change > 0:
        improved.append(f"↑ Completion Rate +{diff.completion_change * 100:.0f}%")
    if diff.deep_work_change and diff.deep_work_change > 0:
        improved.append(f"↑ Deep Work +{diff.deep_work_change * 100:.0f}%")
    if improved:
        lines.append("Improved")
        lines += improved
        lines.append("")

    if diff.declining_topics:
        lines.append("Declining Focus")
        lines += [f"- {t}" for t in diff.declining_topics]
        lines.append("")

    if diff.dormant_topics:
        lines.append("Deprecated")
        lines += [f"- {t}" for t in diff.dormant_topics]
        lines.append("")

    if diff.emerging_topics:
        lines.append("Emerging Interest")
        lines += [f"→ {t}" for t in diff.emerging_topics]
        lines.append("")

    known_issues = []
    if diff.completion_change is not None and diff.completion_change < 0:
        known_issues.append(f"! Completion rate düştü ({diff.completion_change * 100:.0f}%)")
    if active_project_count is not None and active_project_count > KNOWN_ISSUE_MAX_PROJECTS:
        known_issues.append(f"! Aynı anda {active_project_count} aktif proje")
    if known_issues:
        lines.append("Known Issues")
        lines += known_issues
        lines.append("")

    text = "\n".join(lines).rstrip()

    return {
        "base": base_label,
        "target": target_label,
        "text": text,
        "added": diff.added_topics,
        "improved": improved,
        "declining": diff.declining_topics,
        "deprecated": diff.dormant_topics,
        "emerging": diff.emerging_topics,
        "known_issues": known_issues,
    }
