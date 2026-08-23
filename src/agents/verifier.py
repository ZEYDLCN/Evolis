"""Verification Layer — section 21.

Cheap guardrail against hallucinated numbers: every numeric token in the
LLM's answer must trace back to something present in the analysis payload.
Not a full faithfulness classifier (see docs/ARCHITECTURE.md section 37 for
where a real eval harness would plug in), but enough to catch the LLM
inventing a percentage that was never computed.
"""
from __future__ import annotations

import re

_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")


def verify_grounded(answer: str, analysis: dict) -> bool:
    grounded_numbers = _collect_numbers(analysis)
    answer_numbers = {n.replace(",", ".") for n in _NUMBER_RE.findall(answer)}
    unverified = answer_numbers - grounded_numbers
    # Allow small integers (counts, list positions) to pass through freely.
    unverified = {n for n in unverified if not (n.isdigit() and int(n) < 20)}
    return len(unverified) == 0


def _collect_numbers(obj) -> set[str]:
    found: set[str] = set()

    def _walk(value):
        if isinstance(value, bool):
            return
        if isinstance(value, (int, float)):
            found.add(str(round(value, 2)).replace(",", "."))
            found.add(str(round(value * 100, 1)))  # percentage form
        elif isinstance(value, dict):
            for v in value.values():
                _walk(v)
        elif isinstance(value, list):
            for v in value:
                _walk(v)

    _walk(obj)
    return found
