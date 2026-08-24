from src.versions.diff import diff_versions
from src.versions.release_notes import render_release_notes


def test_release_notes_render_matches_spec_shape():
    base = {
        "topic_scores": {"Frontend": 0.6},
        "skill_scores": [],
        "completion_rate": 0.62,
        "deep_work_hours_per_day": 2.1,
        "context_switching_per_day": 7.2,
    }
    target = {
        "topic_scores": {"Frontend": 0.15, "LangGraph": 0.4},
        "skill_scores": [],
        "completion_rate": 0.78,
        "deep_work_hours_per_day": 3.4,
        "context_switching_per_day": 4.1,
    }
    diff = diff_versions(base, target)

    notes = render_release_notes("1.4", "1.7", diff, active_project_count=6)

    assert "YOU v1.4 → YOU v1.7" in notes["text"]
    assert "+ LangGraph" in notes["text"]
    assert any("Completion Rate" in line for line in notes["improved"])
    assert any("active projects" in issue for issue in notes["known_issues"])


def test_release_notes_turkish_mode():
    base = {"topic_scores": {"Frontend": 0.6}, "skill_scores": [], "completion_rate": 0.62}
    target = {"topic_scores": {"Frontend": 0.15, "LangGraph": 0.4}, "skill_scores": [], "completion_rate": 0.78}
    diff = diff_versions(base, target)

    notes = render_release_notes("1.4", "1.7", diff, active_project_count=6, lang="tr")
    assert "Eklenen" in notes["text"]
    assert any("aktif proje" in issue for issue in notes["known_issues"])


def test_release_notes_no_known_issues_when_healthy():
    base = {"topic_scores": {}, "skill_scores": [], "completion_rate": 0.5}
    target = {"topic_scores": {}, "skill_scores": [], "completion_rate": 0.6}
    diff = diff_versions(base, target)

    notes = render_release_notes("1.0", "1.1", diff, active_project_count=1)
    assert notes["known_issues"] == []
