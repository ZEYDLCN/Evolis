from src.agents.classifier import classify_query


def test_classifies_inflected_turkish_forms():
    # Regression: a trailing \b anchor used to silently reject every
    # inflected form of an agglutinative stem (ilgi -> ilgim, değiş ->
    # değiştim), leaving these permanently in the "search" bucket.
    assert classify_query("Hangi konulara ilgim arttı?") == "interest_change"
    assert classify_query("Son 6 ayda nasıl değiştim?") == "interest_change"
    assert classify_query("Projelerimi nasıl yönetiyorum?") == "project_analysis"
    assert classify_query("Neden daha az proje bitiriyorum?") == "behavior_pattern"


def test_classifies_english():
    assert classify_query("How has my interest in AI changed?") == "interest_change"
    assert classify_query("Python vs JavaScript this year") == "comparison"


def test_unmatched_question_falls_back_to_search():
    assert classify_query("Voxera'da ne yaptım?") == "search"
