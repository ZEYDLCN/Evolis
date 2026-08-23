from src.extraction.llm_extractor import HeuristicExtractor


def test_extracts_topics_and_duration():
    extractor = HeuristicExtractor()
    result = extractor.extract(
        "Bugün 2 saat LangGraph çalıştım, Voxera backend'ini geliştirdim. "
        "Deployment tarafına geçemedim çünkü Docker config ile uğraştım."
    )
    assert "LangGraph" in result.topics
    assert result.activities
    assert result.activities[0].duration_minutes == 120
    assert result.blockers
    assert result.completion_status == "blocked"


def test_done_status_detected():
    extractor = HeuristicExtractor()
    result = extractor.extract("Bugün Portfolio projesini tamamladım.")
    assert result.completion_status == "done"


def test_empty_text_has_no_crash():
    extractor = HeuristicExtractor()
    result = extractor.extract("")
    assert result.topics == []
    assert result.completion_status == "none"
