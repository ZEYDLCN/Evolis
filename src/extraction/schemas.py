"""Pydantic contracts for the structured-extraction step.

Kept separate from the API layer's schemas because this shape is also the
"golden dataset" contract used for extraction-accuracy evaluation
(see tests/evaluation).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ActivityType = Literal["learning", "project_development", "practice", "planning", "review"]
CompletionStatus = Literal["done", "partial", "blocked", "none"]


class ExtractedActivity(BaseModel):
    type: ActivityType
    topic: str | None = None
    project: str | None = None
    duration_minutes: int | None = None


class ExtractedEntry(BaseModel):
    """What the LLM (or the deterministic fallback) must produce from raw text."""

    topics: list[str] = Field(default_factory=list)
    activities: list[ExtractedActivity] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    completion_status: CompletionStatus = "none"
