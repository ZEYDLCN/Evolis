"""New-user onboarding checklist — an engagement mechanic, not part of the
original spec. Without it, a fresh account sees "Not enough data yet" on
every screen with no sense of how much further that is — discouraging
exactly when a new user's patience is thinnest. Every step maps to a real
unlock elsewhere in the product (interest scoring needs a handful of
entries, a Version needs some spread of days, a Diff needs two Versions),
so the checklist is describing real thresholds, not made-up busywork.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from src.database.models import Entry, Version

MIN_ENTRIES_FOR_INTERESTS = 3
MIN_DISTINCT_DAYS_FOR_VERSION = 7


@dataclass
class OnboardingStep:
    key: str
    label: str
    done: bool
    progress: int
    target: int


@dataclass
class OnboardingStatus:
    steps: list[OnboardingStep] = field(default_factory=list)

    @property
    def all_done(self) -> bool:
        return all(s.done for s in self.steps)

    def to_dict(self) -> dict:
        return {
            "all_done": self.all_done,
            "steps": [
                {"key": s.key, "label": s.label, "done": s.done, "progress": s.progress, "target": s.target}
                for s in self.steps
            ],
        }


_LABELS = {
    "first_entry": {"en": "Write your first entry", "tr": "İlk kaydını yaz"},
    "three_entries": {"en": "Log 3 entries to unlock Interest Drift", "tr": "İlgi Alanları Analizini açmak için 3 kayıt gir"},
    "week_of_days": {
        "en": "Log across 7 different days to unlock your first Version",
        "tr": "İlk Versiyonunu açmak için 7 farklı günde kayıt gir",
    },
    "first_version": {"en": "Generate your first Version", "tr": "İlk Versiyonunu oluştur"},
    "first_diff": {"en": "Generate a second Version to compare with Diff", "tr": "Karşılaştırmak için ikinci bir Versiyon oluştur"},
}


def compute_onboarding_status(db: Session, user_id: str, lang: str = "en") -> OnboardingStatus:
    entries = db.query(Entry.entry_date).filter(Entry.user_id == user_id).all()
    entry_count = len(entries)
    distinct_days = len({(e.date() if isinstance(e, dt.datetime) else e) for (e,) in entries})
    version_count = db.query(Version).filter(Version.user_id == user_id).count()

    def label(key: str) -> str:
        return _LABELS[key]["tr" if lang == "tr" else "en"]

    steps = [
        OnboardingStep(
            key="first_entry",
            label=label("first_entry"),
            done=entry_count >= 1,
            progress=min(entry_count, 1),
            target=1,
        ),
        OnboardingStep(
            key="three_entries",
            label=label("three_entries"),
            done=entry_count >= MIN_ENTRIES_FOR_INTERESTS,
            progress=min(entry_count, MIN_ENTRIES_FOR_INTERESTS),
            target=MIN_ENTRIES_FOR_INTERESTS,
        ),
        OnboardingStep(
            key="week_of_days",
            label=label("week_of_days"),
            done=distinct_days >= MIN_DISTINCT_DAYS_FOR_VERSION,
            progress=min(distinct_days, MIN_DISTINCT_DAYS_FOR_VERSION),
            target=MIN_DISTINCT_DAYS_FOR_VERSION,
        ),
        OnboardingStep(
            key="first_version",
            label=label("first_version"),
            done=version_count >= 1,
            progress=min(version_count, 1),
            target=1,
        ),
        OnboardingStep(
            key="first_diff",
            label=label("first_diff"),
            done=version_count >= 2,
            progress=min(version_count, 2),
            target=2,
        ),
    ]

    return OnboardingStatus(steps=steps)
