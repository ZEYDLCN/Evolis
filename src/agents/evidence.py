"""Evidence/grounding summary for Ask Evolis — section 13.

Turns the same analysis payload the answer was generated from into a small,
honest "what this is based on" block: how many entries were analyzed, a
few factual bullet points (never invented deltas — only numbers actually
present in the analysis), and, when semantic search ran, the source
entries a "View source entries" panel can expand into.
"""
from __future__ import annotations


def build_evidence(analysis: dict, lang: str = "en") -> dict:
    entries_analyzed = analysis.get("entries_analyzed", 0)

    bullets: list[str] = []
    interests: dict = analysis.get("interests") or {}
    for topic, score in list(interests.items())[:3]:
        bullets.append(
            f"{topic} ilgi skoru: %{round(score * 100)}" if lang == "tr" else f"{topic} interest score: {round(score * 100)}%"
        )

    skills: list = analysis.get("skills") or []
    for skill in skills[:2]:
        bullets.append(
            f"{skill['skill']} beceri aktivitesi: {skill['activity_score']}/100"
            if lang == "tr"
            else f"{skill['skill']} skill activity: {skill['activity_score']}/100"
        )

    source_entries = [hit["text"] for hit in (analysis.get("retrieved_entries") or [])]
    if source_entries and not bullets:
        bullets.append(
            f"{len(source_entries)} ilgili geçmiş kayıt bulundu" if lang == "tr" else f"Found {len(source_entries)} related past entries"
        )

    return {
        "entries_analyzed": entries_analyzed,
        "bullets": bullets,
        "source_entries": source_entries,
    }
