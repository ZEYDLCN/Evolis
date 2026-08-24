"""Single place that picks and calls whichever LLM provider is configured.

Before this module existed, extraction (src/extraction/llm_extractor.py),
Ask Evolis explanations (src/agents/orchestrator.py), and cluster naming
(src/ml/clustering/naming.py) each independently checked ANTHROPIC_API_KEY
and hand-rolled an `import anthropic; client = anthropic.Anthropic()` call.
Adding a second provider meant repeating that three times — this collapses
it to one routing function, so a caller just does:

    from src.llm.provider import complete, LLMNotConfigured
    try:
        raw = complete(SYSTEM_PROMPT, user_text)
    except Exception:
        ...deterministic fallback...

Precedence when multiple keys are set: GROQ_API_KEY > ANTHROPIC_API_KEY.
Groq first because it's usually the cheaper/faster choice when both are
configured; there's no other significance to the order. Metrics stay owned
by each call site (purpose="extraction" vs "ask_explain" vs
"cluster_naming") rather than living here, matching the pattern already
used throughout the codebase — this module only ever raises, never records.
"""
from __future__ import annotations

import os

import httpx

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMNotConfigured(Exception):
    """Neither GROQ_API_KEY nor ANTHROPIC_API_KEY is set."""


def active_provider() -> str | None:
    """Which provider `complete()` would use right now, or None if neither
    is configured. Callers use this to decide whether to attempt an LLM
    call at all before doing other setup work (see orchestrator.py)."""
    if GROQ_API_KEY:
        return "groq"
    if ANTHROPIC_API_KEY:
        return "anthropic"
    return None


def complete(system: str, user: str, max_tokens: int = 1024) -> str:
    """One request/response LLM call. Raises LLMNotConfigured if no
    provider is configured, or whatever the underlying client/HTTP call
    raises on failure (a timeout, a 4xx/5xx, ...) -- always let the caller
    decide what "no usable answer" means for it (usually: fall back to the
    deterministic heuristic already sitting right next to the call site)."""
    provider = active_provider()
    if provider == "groq":
        return _complete_groq(system, user, max_tokens)
    if provider == "anthropic":
        return _complete_anthropic(system, user, max_tokens)
    raise LLMNotConfigured


def _complete_groq(system: str, user: str, max_tokens: int) -> str:
    # Groq exposes an OpenAI-compatible Chat Completions endpoint, so a
    # plain HTTP POST (via httpx, already a base dependency) is enough --
    # no groq/openai SDK needed for a single-turn, non-streaming call.
    response = httpx.post(
        GROQ_CHAT_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": GROQ_MODEL,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _complete_anthropic(system: str, user: str, max_tokens: int) -> str:
    import anthropic  # local import: optional dependency

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
