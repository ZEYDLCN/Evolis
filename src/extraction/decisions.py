"""Decision-signal detection — "Evolution Forks" (Turning Points feature).

A user rarely announces a decision in a structured way; they just write
about it: "Bu ay frontend yerine AI Engineering'e ağırlık vermeye karar
verdim." This is a small deterministic keyword/pattern matcher — not an
LLM call — that recognizes decision-marker phrasing and, when an
"X yerine Y" / "Y instead of X" contrast is present, pulls out the two
sides as alternatives. It's intentionally conservative: most decision
sentences won't parse cleanly into alternatives, and that's fine — a
title-only decision event is still useful, and nothing here fabricates
a choice the user didn't actually state.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_DECISION_MARKERS = [
    "karar verdim",
    "karar aldım",
    "ağırlık vermeye karar",
    "decided to",
    "decided that",
    "i've decided",
    "i decided",
    "made a decision to",
]

# "X yerine Y'ye ağırlık ver" / "Y instead of X" — captures (alternative, chosen).
# Bounded to 1-3 words immediately adjacent to the trigger so a leading
# "Bu ay ..." or "I decided to ..." clause doesn't get swept into the capture.
_WORD = r"[A-Za-zÇĞİÖŞÜçğıöşü]+"
_TR_INSTEAD_RE = re.compile(
    rf"({_WORD})\s+yerine\s+({_WORD}(?:\s+{_WORD}){{0,2}})'?[a-zçğıöşü]*\s*(?:ağırlık ver|odaklan|geç)",
    re.IGNORECASE,
)
_EN_INSTEAD_RE = re.compile(
    rf"focus(?:ing)? on\s+({_WORD}(?:\s+{_WORD}){{0,3}})\s+instead of\s+({_WORD}(?:\s+{_WORD}){{0,3}})",
    re.IGNORECASE,
)


@dataclass
class DecisionSignal:
    title: str
    alternatives: list[str]
    chosen: str | None


def detect_decision_signal(text: str) -> DecisionSignal | None:
    lowered = text.lower()
    if not any(marker in lowered for marker in _DECISION_MARKERS):
        return None

    # Trim to a clause-length title — the raw entry can be several sentences.
    title = text.strip().split(".")[0].strip()
    if len(title) > 140:
        title = title[:140].rstrip() + "…"

    match = _TR_INSTEAD_RE.search(text)
    if match:
        alternative, chosen = match.group(1).strip(), match.group(2).strip()
        return DecisionSignal(title=title, alternatives=[alternative, chosen], chosen=chosen)

    match = _EN_INSTEAD_RE.search(text)
    if match:
        chosen, alternative = match.group(1).strip(), match.group(2).strip()
        return DecisionSignal(title=title, alternatives=[alternative, chosen], chosen=chosen)

    return DecisionSignal(title=title, alternatives=[], chosen=None)
