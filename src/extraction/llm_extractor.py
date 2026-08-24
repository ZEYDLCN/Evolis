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

from src.monitoring.metrics import llm_calls_total

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
as short canonical nouns (e.g. "LangGraph", "Docker", "English", "Reading",
"Walking", "Presentation"), not full sentences. This log covers a person's
whole life, not just technical work — capture skills, habits/routines
(exercise, sleep, walking), personal growth (reading, hobbies, creative
work), and work/career topics (meetings, presentations, projects) exactly
as readily as programming/AI topics. Don't skip a topic just because it
isn't technical."""


class Extractor(Protocol):
    def extract(self, text: str) -> ExtractedEntry: ...


class AnthropicExtractor:
    def __init__(self, model: str = "claude-sonnet-5") -> None:
        import anthropic  # local import: optional dependency

        self._client = anthropic.Anthropic()
        self._model = model

    def extract(self, text: str) -> ExtractedEntry:
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": text}],
            )
            raw = "".join(block.text for block in response.content if block.type == "text")
            data = json.loads(_strip_code_fence(raw))
            result = ExtractedEntry.model_validate(data)
        except Exception:
            llm_calls_total.labels(purpose="extraction", outcome="error").inc()
            raise
        llm_calls_total.labels(purpose="extraction", outcome="success").inc()
        return result


_DURATION_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(saat|hour|hr|dakika|dk|min)", re.IGNORECASE)

# Broader life tracking (not just tech): common lowercase nouns for a
# life-domain activity that the plain "capitalized token" heuristic below
# would otherwise miss entirely — most of a habits/personal-growth entry
# never gets capitalized ("yürüdüm", "kitap okudum").
_LIFE_TOPIC_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bingilizce\b|\benglish\b", re.IGNORECASE), "English"),
    (re.compile(r"\byürü|\bwalk(?:ing)?\b", re.IGNORECASE), "Walking"),
    (re.compile(r"\bkoş|\brun(?:ning)?\b", re.IGNORECASE), "Running"),
    (re.compile(r"\begzersiz|\bexercise\b|\bworkout\b|\bspor\b|\bgym\b", re.IGNORECASE), "Exercise"),
    (re.compile(r"\bkitap\b|\bbook\b|\boku(?:dum|yorum|ma)?\b|\bread(?:ing)?\b", re.IGNORECASE), "Reading"),
    (re.compile(r"\buyku\b|\bsleep\b", re.IGNORECASE), "Sleep"),
    (re.compile(r"\bsunum\b|\bpresentation\b", re.IGNORECASE), "Presentation"),
    (re.compile(r"\btoplant[ıi]\b|\bmeeting\b", re.IGNORECASE), "Meeting"),
    (re.compile(r"\bmeditasyon\b|\bmeditat(?:e|ion|ing)\b", re.IGNORECASE), "Meditation"),
    (re.compile(r"\bjournal(?:ing)?\b|\bgünlük\b", re.IGNORECASE), "Journaling"),
]
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
        seen: list[str] = []

        # Life-domain nouns first (usually lowercase, e.g. "yürüdüm",
        # "kitap okudum") — these are the ones a pure capitalization
        # heuristic would silently drop, and Evolis is meant to track more
        # than tech work.
        for pattern, canonical in _LIFE_TOPIC_PATTERNS:
            if pattern.search(text) and canonical not in seen:
                seen.append(canonical)

        # Known-tech capitalized tokens, plus generic CamelCase / ALLCAPS words.
        candidates = re.findall(r"\b([A-Z][a-zA-Z0-9]{2,}(?:\s[A-Z][a-zA-Z0-9]{2,})?)\b", text)
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
