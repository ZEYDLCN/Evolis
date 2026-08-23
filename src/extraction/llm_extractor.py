"""LLM-backed structured extraction, per the project's core principle:

    LLM != Analytics Engine

The LLM's only job here is turning free text into the ExtractedEntry shape.
All downstream metrics (interest scores, skill scores, completion rate, ...)
are computed deterministically from that structured output — never guessed
by a model.

Two backends:
  - AnthropicExtractor: calls the Claude API with a JSON-schema-constrained
    prompt. Used when ANTHROPIC_API_KEY is set.
  - HeuristicExtractor: a zero-dependency regex/keyword fallback so the
    pipeline (and tests) run offline and for free.

get_extractor() picks whichever is available; callers should depend on the
`Extractor` protocol, not a concrete class.
"""
from __future__ import annotations

import json
import os
import re
from typing import Protocol

from .schemas import ExtractedActivity, ExtractedEntry

SYSTEM_PROMPT = """You extract structured data from a personal daily activity log.
Return ONLY a JSON object matching this shape, no prose:
{
  "topics": [string],
  "activities": [{"type": "learning|project_development|practice|planning|review",
                   "topic": string|null, "project": string|null,
                   "duration_minutes": int|null}],
  "blockers": [string],
  "completion_status": "done|partial|blocked|none"
}
The entry may be in Turkish or English. Topic/project names should be kept
as short canonical nouns (e.g. "LangGraph", "Docker"), not full sentences."""


class Extractor(Protocol):
    def extract(self, text: str) -> ExtractedEntry: ...


class AnthropicExtractor:
    def __init__(self, model: str = "claude-sonnet-5") -> None:
        import anthropic  # local import: optional dependency

        self._client = anthropic.Anthropic()
        self._model = model

    def extract(self, text: str) -> ExtractedEntry:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text}],
        )
        raw = "".join(block.text for block in response.content if block.type == "text")
        data = json.loads(_strip_code_fence(raw))
        return ExtractedEntry.model_validate(data)


_DURATION_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(saat|hour|hr|dakika|dk|min)", re.IGNORECASE)
_BLOCKER_MARKERS = ("uğraştım", "geçemedim", "blocked", "sorun", "engel", "yapamadım")
_DONE_MARKERS = ("bitirdim", "tamamladım", "done", "completed", "finished")
_PARTIAL_MARKERS = ("kısmen", "biraz", "partial", "devam ediyor", "geçemedim")


class HeuristicExtractor:
    """Deterministic fallback: capitalized/quoted tokens as topics, regex durations.

    Deliberately simple — this exists so the pipeline works with zero API
    keys and so unit tests don't need network access. Swap in
    AnthropicExtractor for real accuracy.
    """

    def extract(self, text: str) -> ExtractedEntry:
        topics = self._guess_topics(text)
        duration = self._guess_duration_minutes(text)
        blockers = [text] if any(m in text.lower() for m in _BLOCKER_MARKERS) else []

        status: str = "none"
        lowered = text.lower()
        if any(m in lowered for m in _DONE_MARKERS):
            status = "done"
        elif blockers or any(m in lowered for m in _PARTIAL_MARKERS):
            status = "partial" if not blockers else "blocked"

        activities = []
        if topics or duration is not None:
            activities.append(
                ExtractedActivity(
                    type="learning" if not blockers else "project_development",
                    topic=topics[0] if topics else None,
                    duration_minutes=duration,
                )
            )

        return ExtractedEntry(
            topics=topics,
            activities=activities,
            blockers=blockers,
            completion_status=status,  # type: ignore[arg-type]
        )

    @staticmethod
    def _guess_topics(text: str) -> list[str]:
        # Known-tech capitalized tokens, plus generic CamelCase / ALLCAPS words.
        candidates = re.findall(r"\b([A-Z][a-zA-Z0-9]{2,}(?:\s[A-Z][a-zA-Z0-9]{2,})?)\b", text)
        seen: list[str] = []
        for c in candidates:
            if c not in seen and c.lower() not in {"bugün", "ben", "the", "today"}:
                seen.append(c)
        return seen[:8]

    @staticmethod
    def _guess_duration_minutes(text: str) -> int | None:
        match = _DURATION_RE.search(text)
        if not match:
            return None
        value = float(match.group(1).replace(",", "."))
        unit = match.group(2).lower()
        if unit.startswith(("saat", "hour", "hr")):
            return int(value * 60)
        return int(value)


def _strip_code_fence(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        raw = raw.removeprefix("json").strip()
    return raw


def get_extractor() -> Extractor:
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            return AnthropicExtractor()
        except Exception:
            pass
    return HeuristicExtractor()
