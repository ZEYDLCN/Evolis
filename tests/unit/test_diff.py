from src.versions.diff import diff_versions


def test_diff_detects_added_declining_and_dormant_topics():
    base = {
        "topic_scores": {"Frontend": 0.6, "React": 0.5, "Docker": 0.1},
        "skill_scores": [{"skill": "Python", "activity_score": 50}],
        "completion_rate": 0.62,
        "deep_work_hours_per_day": 2.1,
        "context_switching_per_day": 7.2,
    }
    target = {
        "topic_scores": {"Frontend": 0.2, "LangGraph": 0.4, "Docker": 0.02},
        "skill_scores": [{"skill": "Python", "activity_score": 76}, {"skill": "RAG", "activity_score": 81}],
        "completion_rate": 0.78,
        "deep_work_hours_per_day": 3.4,
        "context_switching_per_day": 4.1,
    }

    diff = diff_versions(base, target)

    assert "LangGraph" in diff.added_topics
    assert "Frontend" in diff.declining_topics
    assert "Docker" in diff.dormant_topics
    assert diff.skill_changes["RAG"]["before"] == 0
    assert diff.skill_changes["Python"]["change"] == 26
    assert diff.completion_change == round(0.78 - 0.62, 4)
    assert diff.deep_work_change > 0
    assert diff.context_switching_change < 0
    assert diff.deep_work_before == 2.1
    assert diff.deep_work_after == 3.4
    assert diff.completion_before == 0.62
    assert diff.completion_after == 0.78
    assert diff.topic_domains["LangGraph"] == "Skills"
