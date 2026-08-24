from src.agents.evidence import build_evidence


def test_evidence_includes_entries_analyzed_and_interest_bullets():
    analysis = {
        "entries_analyzed": 17,
        "interests": {"RAG": 0.6, "LangGraph": 0.4},
        "skills": [{"skill": "Python", "activity_score": 80}],
    }
    evidence = build_evidence(analysis)

    assert evidence["entries_analyzed"] == 17
    assert any("RAG" in b for b in evidence["bullets"])
    assert any("Python" in b for b in evidence["bullets"])
    assert evidence["source_entries"] == []


def test_evidence_falls_back_to_retrieved_entry_count():
    analysis = {"entries_analyzed": 0, "retrieved_entries": [{"text": "a"}, {"text": "b"}]}
    evidence = build_evidence(analysis)

    assert evidence["source_entries"] == ["a", "b"]
    assert "Found 2 related past entries" in evidence["bullets"]


def test_evidence_handles_empty_analysis():
    evidence = build_evidence({})
    assert evidence == {"entries_analyzed": 0, "bullets": [], "source_entries": []}
