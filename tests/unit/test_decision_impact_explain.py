from src.agents.orchestrator import _explain_ranked_decisions, _template_explain


def test_no_causal_language_and_no_counterfactual():
    ranked = [
        {
            "event": {"title": "Focus on AI Engineering"},
            "magnitude": 0.42,
            "top_change": {"topic": "AI Engineering", "before": 0.1, "after": 0.5, "change": 0.4},
        },
    ]
    answer = _explain_ranked_decisions(ranked, "en")
    assert "coincide" in answer
    assert "caused" not in answer.lower()
    assert "would have" not in answer.lower()
    assert "Focus on AI Engineering" in answer
    assert "AI Engineering interest shifted +40 pts" in answer


def test_turkish_phrasing_avoids_causal_claim():
    ranked = [{"event": {"title": "AI Engineering'e ağırlık ver"}, "magnitude": 0.3, "top_change": None}]
    answer = _explain_ranked_decisions(ranked, "tr")
    assert "sebep oldu" not in answer
    assert "nedensellik iddiası değildir" in answer


def test_empty_ranking_says_not_enough_data():
    assert "enough" in _explain_ranked_decisions([], "en").lower()


def test_template_explain_routes_ranked_decisions():
    ranked = [{"event": {"title": "X"}, "magnitude": 0.1, "top_change": None}]
    answer = _template_explain({"ranked_decisions": ranked}, "en")
    assert "coincide" in answer
