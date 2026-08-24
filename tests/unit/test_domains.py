from src.extraction.domains import DOMAIN_LABELS, classify_domain, detect_behavior_signals


def test_classify_known_life_domain_topics():
    assert classify_domain("English") == "learning"
    assert classify_domain("Walking") == "habits_routines"
    assert classify_domain("Reading") == "personal_growth"
    assert classify_domain("Presentation") == "skills"
    assert classify_domain("Meeting") == "work_projects"


def test_classify_falls_back_to_skills_for_unknown_proper_nouns():
    assert classify_domain("Voxera") == "skills"
    assert classify_domain("LangGraph") == "skills"


def test_behavior_signal_labels_classify_as_behavior():
    assert classify_domain("Low Focus") == "behavior"
    assert classify_domain("Low Energy") == "behavior"


def test_detect_behavior_signals_matches_user_examples():
    assert detect_behavior_signals("Bugün akşam kitap okudum ama odaklanmakta zorlandım.") == ["Low Focus"]
    assert detect_behavior_signals("Son 2 haftadır işten sonra hiçbir şey yapacak enerjim kalmıyor.") == ["Low Energy"]
    assert detect_behavior_signals("Bugün toplantıda sunumu ben yaptım, eskisine göre çok daha rahattım.") == ["High Confidence"]


def test_detect_behavior_signals_empty_for_neutral_text():
    assert detect_behavior_signals("Bugün Docker ile uğraştım.") == []


def test_domain_labels_cover_every_classify_output():
    for topic in ["English", "Walking", "Reading", "Presentation", "Meeting", "Unknown Thing", "Low Focus"]:
        assert classify_domain(topic) in DOMAIN_LABELS
