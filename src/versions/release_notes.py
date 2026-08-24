"""Release Notes For You — section 28.

Pure formatting over an already-computed VersionDiff: no LLM, no new
numbers, just the changelog-style rendering the product spec shows as the
shareable card. (An actual image/card renderer is a frontend concern —
this returns the structured text a client renders however it likes.)
"""
from __future__ import annotations

from src.versions.diff import VersionDiff

KNOWN_ISSUE_MAX_PROJECTS = 4  # active projects touched in the target period considered a "Known Issue"

_SECTION_LABELS = {
    "en": {"added": "Added", "improved": "Improved", "declining": "Declining Focus", "deprecated": "Deprecated", "emerging": "Emerging Interest", "known_issues": "Known Issues"},
    "tr": {"added": "Eklenen", "improved": "İyileşen", "declining": "Azalan Odak", "deprecated": "Bırakılan", "emerging": "Yükselen İlgi", "known_issues": "Dikkat Edilecekler"},
}


def render_release_notes(
    base_label: str, target_label: str, diff: VersionDiff, active_project_count: int | None = None, lang: str = "en"
) -> dict:
    labels = _SECTION_LABELS["tr" if lang == "tr" else "en"]
    lines = [f"YOU v{base_label} → YOU v{target_label}", ""]

    if diff.added_topics:
        lines.append(labels["added"])
        lines += [f"+ {t}" for t in diff.added_topics]
        lines.append("")

    improved = []
    completion_label = "Tamamlanma Oranı" if lang == "tr" else "Completion Rate"
    deep_work_label = "Derin Çalışma" if lang == "tr" else "Deep Work"
    if diff.completion_change and diff.completion_change > 0:
        improved.append(f"↑ {completion_label} +{diff.completion_change * 100:.0f}%")
    if diff.deep_work_change and diff.deep_work_change > 0:
        improved.append(f"↑ {deep_work_label} +{diff.deep_work_change * 100:.0f}%")
    if improved:
        lines.append(labels["improved"])
        lines += improved
        lines.append("")

    if diff.declining_topics:
        lines.append(labels["declining"])
        lines += [f"- {t}" for t in diff.declining_topics]
        lines.append("")

    if diff.dormant_topics:
        lines.append(labels["deprecated"])
        lines += [f"- {t}" for t in diff.dormant_topics]
        lines.append("")

    if diff.emerging_topics:
        lines.append(labels["emerging"])
        lines += [f"→ {t}" for t in diff.emerging_topics]
        lines.append("")

    known_issues = []
    if diff.completion_change is not None and diff.completion_change < 0:
        known_issues.append(
            f"! Tamamlanma oranı düştü (%{diff.completion_change * 100:.0f})"
            if lang == "tr"
            else f"! Completion rate dropped ({diff.completion_change * 100:.0f}%)"
        )
    if active_project_count is not None and active_project_count > KNOWN_ISSUE_MAX_PROJECTS:
        known_issues.append(
            f"! Aynı anda {active_project_count} aktif proje" if lang == "tr" else f"! {active_project_count} active projects at once"
        )
    if known_issues:
        lines.append(labels["known_issues"])
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
