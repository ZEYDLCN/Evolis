from src.versions.diff import diff_versions
from src.versions.release_notes import render_release_notes
from src.versions.share_card import render_release_notes_svg


def _sample_notes() -> dict:
    base = {"topic_scores": {"Frontend": 0.6}, "skill_scores": [], "completion_rate": 0.62}
    target = {"topic_scores": {"Frontend": 0.1, "LangGraph": 0.4}, "skill_scores": [], "completion_rate": 0.78}
    diff = diff_versions(base, target)
    return render_release_notes("1.4", "1.7", diff, active_project_count=6)


def test_svg_is_well_formed_and_contains_content():
    svg = render_release_notes_svg(_sample_notes())

    assert svg.startswith("<svg")
    assert svg.strip().endswith("</svg>")
    assert "LifeDiff" in svg
    assert "YOU v1.4" in svg
    assert "LangGraph" in svg


def test_svg_escapes_untrusted_looking_text():
    notes = _sample_notes()
    notes["added"] = ['<script>alert(1)</script>']
    svg = render_release_notes_svg(notes)
    assert "<script>" not in svg
    assert "&lt;script&gt;" in svg
