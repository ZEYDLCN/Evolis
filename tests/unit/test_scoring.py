from src.ml.scoring.interest_score import InterestSignal, compute_interest_score, recency_score
from src.ml.scoring.skill_score import SkillSignal, compute_skill_score


def test_interest_score_bounds():
    low = InterestSignal(0, 0, 0, 0, 0)
    high = InterestSignal(1, 1, 1, 1, 1)
    assert compute_interest_score(low) == 0.0
    assert compute_interest_score(high) == 1.0


def test_recency_score_decays():
    assert recency_score(0) == 1.0
    assert recency_score(21) < 0.6  # ~half-life
    assert recency_score(21) > 0.4


def test_skill_score_scales_to_100():
    signal = SkillSignal(1, 1, 1, 1, 1)
    assert compute_skill_score(signal) == 100
    assert compute_skill_score(SkillSignal(0, 0, 0, 0, 0)) == 0
