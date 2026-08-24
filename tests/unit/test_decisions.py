from src.extraction.decisions import detect_decision_signal


def test_detects_turkish_decision_with_alternatives():
    signal = detect_decision_signal("Bu ay frontend yerine AI Engineering'e ağırlık vermeye karar verdim.")
    assert signal is not None
    assert signal.alternatives == ["frontend", "AI Engineering"]
    assert signal.chosen == "AI Engineering"


def test_detects_english_decision_with_alternatives():
    signal = detect_decision_signal("I decided to focus on AI Engineering instead of Backend Engineering.")
    assert signal is not None
    assert signal.chosen == "AI Engineering"
    assert "Backend Engineering" in signal.alternatives


def test_detects_decision_without_alternatives():
    signal = detect_decision_signal("Simultaneous proje sayısını azaltmaya karar verdim.")
    assert signal is not None
    assert signal.alternatives == []
    assert signal.chosen is None


def test_no_decision_in_neutral_text():
    assert detect_decision_signal("Bugün Docker ile uğraştım.") is None


def test_title_truncated_to_first_sentence():
    signal = detect_decision_signal("Karar verdim. Bugün ayrıca RAG üzerine çok çalıştım ve yoruldum.")
    assert signal is not None
    assert signal.title == "Karar verdim"
