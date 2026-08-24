"""Life Domain taxonomy — the product's broader positioning: Evolis tracks
how a person changes overall, not just their tech skills.

Every topic Evolis has ever extracted (from a project name to "Reading" to
a behavior signal like "Low Focus") gets classified into one of five life
domains, plus a sixth "behavior" bucket for signals that describe a state
rather than an activity. Classification is a small deterministic keyword
lookup — not an LLM call — so it's free, instant, and reproducible: the
same topic name always lands in the same domain. This keeps the core
"LLM != Analytics Engine" principle intact one layer further out.

This is a v1 keyword classifier, not real NLP — an unfamiliar proper noun
(a tool name, a project name) falls through to "skills" by default, which
is usually the right call for anything Evolis can't otherwise place.
"""
from __future__ import annotations

DOMAIN_LABELS: dict[str, str] = {
    "skills": "Skills",
    "work_projects": "Work & Projects",
    "learning": "Learning",
    "habits_routines": "Habits & Routines",
    "personal_growth": "Personal Growth",
    "behavior": "Behavior",
}

# Order used wherever domains are rendered as sections (release notes,
# grouped diffs, insights) — behavior signals last since they're states,
# not areas of growth.
DOMAIN_ORDER: list[str] = ["skills", "work_projects", "learning", "habits_routines", "personal_growth", "behavior"]

_KEYWORDS: dict[str, list[str]] = {
    "learning": [
        "english", "ingilizce", "course", "kurs", "study", "çalış", "learn", "öğren",
        "language", "dil", "practice", "pratik", "certificate", "sertifika", "lesson", "ders",
        "vocabulary", "kelime", "spanish", "german", "almanca", "ispanyolca",
    ],
    "habits_routines": [
        "walk", "yürü", "run", "koş", "exercise", "egzersiz", "spor", "gym", "workout",
        "sleep", "uyku", "diet", "beslen", "routine", "rutin", "meditat", "morning routine",
        "sabah rutini", "yoga", "stretch", "hydrat",
    ],
    "personal_growth": [
        "read", "oku", "kitap", "book", "journal", "günlük", "hobby", "hobi", "creative",
        "yaratıcı", "art", "sanat", "music", "müzik", "paint", "resim", "instrument", "enstrüman",
        "podcast", "meditation", "mindfulness",
    ],
    "work_projects": [
        "proje", "project", "develop", "geliştir", "ship", "feature", "release", "deploy",
        "backend", "frontend", "api", "sprint", "meeting", "toplantı", "client", "müşteri",
        "startup", "girişim", "product", "ürün",
    ],
    "skills": [
        "presentation", "sunum", "speak", "konuş", "communicat", "iletişim", "confiden",
        "özgüven", "design", "tasarım", "leadership", "liderlik", "negotiat", "public speaking",
        "writing", "yazma",
    ],
}

# Exact-match labels for behavior signals detected from free text (see
# detect_behavior_signals below) — these always classify as "behavior"
# regardless of what words happen to be in the label.
_BEHAVIOR_SIGNAL_MARKERS: dict[str, list[str]] = {
    "Low Focus": [
        "odaklanamadım", "dikkatim dağıldı", "couldn't focus", "struggled to focus", "hard to focus",
        "zorlandım odaklanmakta", "odaklanmakta zorlandım", "odaklanmakta güçlük",
    ],
    "Low Energy": [
        "enerjim kalmadı", "enerjim kalmıyor", "enerjim yok", "yorgunum", "bitkin", "exhausted",
        "no energy left", "drained", "hiçbir şey yapacak enerjim",
    ],
    "High Confidence": ["rahat hissettim", "özgüvenliydim", "felt confident", "more confident", "daha rahattım"],
    "Low Social Activity": ["kimseyle görüşmedim", "yalnız hissettim", "didn't see anyone", "felt isolated"],
}


def classify_domain(topic: str) -> str:
    """Returns a domain key from DOMAIN_LABELS for a topic name. Pure and
    stateless — same input always gives the same output, no DB lookup."""
    if topic in _BEHAVIOR_SIGNAL_MARKERS:
        return "behavior"

    lowered = topic.lower()
    for domain, keywords in _KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return domain
    return "skills"


def detect_behavior_signals(text: str) -> list[str]:
    """Scans raw entry text for behavior-signal phrases (section: broader
    life tracking). Returned as plain topic labels — see entry_service.py,
    which stores them as ordinary EntryTopic rows so they flow through
    every existing pipeline (interest scores, diffs, Ask Evolis) with zero
    new infrastructure. Never framed as a diagnosis — just a phrase match."""
    lowered = text.lower()
    return [label for label, markers in _BEHAVIOR_SIGNAL_MARKERS.items() if any(m in lowered for m in markers)]
