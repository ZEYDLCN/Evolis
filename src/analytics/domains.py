"""Life Domain rollup — groups the existing per-topic interest scores
(src/analytics/interests.py) under the five life domains plus Behavior
(src/extraction/domains.py). No new signal is computed here: this is a
pure grouping/relabeling layer so the product can present "Skills /
Work & Projects / Learning / Habits & Routines / Personal Growth" instead
of a flat topic list, without duplicating any scoring logic.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from src.analytics.interests import topic_interest_scores
from src.extraction.domains import DOMAIN_ORDER, classify_domain, domain_label


def domain_breakdown(db: Session, user_id: str, start: dt.datetime, end: dt.datetime, lang: str = "en") -> dict:
    scores = topic_interest_scores(db, user_id, start, end)

    grouped: dict[str, dict[str, float]] = {domain: {} for domain in DOMAIN_ORDER}
    for topic, score in scores.items():
        grouped[classify_domain(topic)][topic] = score

    return {
        domain_label(domain, lang): dict(sorted(topics.items(), key=lambda kv: kv[1], reverse=True))
        for domain in DOMAIN_ORDER
        if (topics := grouped[domain])
    }
