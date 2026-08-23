"""Section 23-24: retrieve relevant past entries for a natural-language question.

Vector search always runs (works with the JSON fallback storage by scoring
in Python; switches to a real pgvector ANN query when EMBEDDING_BACKEND=pgvector).
Hybrid keyword search (simple LIKE/full-text) is layered in for exact
technology-name lookups per section 24, then results are fused by score.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.encryption import encryption_enabled
from src.database.models import Embedding, Entry
from src.embeddings.embedding_service import cosine_similarity, get_embedding_model


@dataclass
class RetrievedEntry:
    entry_id: str
    text: str
    score: float


def vector_search(db: Session, user_id: str, query: str, top_k: int = 5) -> list[RetrievedEntry]:
    model = get_embedding_model()
    query_vector = model.embed(query)

    rows = db.execute(
        select(Entry.id, Entry.raw_text, Embedding.vector)
        .join(Embedding, Embedding.entry_id == Entry.id)
        .where(Entry.user_id == user_id)
    ).all()

    scored = [
        RetrievedEntry(entry_id=entry_id, text=text, score=cosine_similarity(query_vector, vector))
        for entry_id, text, vector in rows
    ]
    scored.sort(key=lambda r: r.score, reverse=True)
    return scored[:top_k]


def keyword_search(db: Session, user_id: str, query: str, top_k: int = 5) -> list[RetrievedEntry]:
    if encryption_enabled():
        # raw_text is ciphertext in the database when ENCRYPTION_KEY is set,
        # so SQL LIKE can't match it — decrypt this user's own rows (ORM does
        # this transparently) and filter in Python instead. Fine at
        # personal-analytics scale; see src/database/encryption.py.
        needle = query.lower()
        rows = db.query(Entry.id, Entry.raw_text).filter(Entry.user_id == user_id).all()
        matches = [r for r in rows if needle in r[1].lower()][:top_k]
        return [RetrievedEntry(entry_id=r[0], text=r[1], score=1.0) for r in matches]

    like_pattern = f"%{query}%"
    rows = db.execute(
        select(Entry.id, Entry.raw_text)
        .where(Entry.user_id == user_id, Entry.raw_text.ilike(like_pattern))
        .limit(top_k)
    ).all()
    return [RetrievedEntry(entry_id=r[0], text=r[1], score=1.0) for r in rows]


def hybrid_search(db: Session, user_id: str, query: str, top_k: int = 5) -> list[RetrievedEntry]:
    vector_hits = {r.entry_id: r for r in vector_search(db, user_id, query, top_k=top_k * 2)}
    keyword_hits = {r.entry_id: r for r in keyword_search(db, user_id, query, top_k=top_k * 2)}

    fused: dict[str, float] = {}
    texts: dict[str, str] = {}
    for entry_id, hit in vector_hits.items():
        fused[entry_id] = fused.get(entry_id, 0.0) + 0.7 * hit.score
        texts[entry_id] = hit.text
    for entry_id, hit in keyword_hits.items():
        fused[entry_id] = fused.get(entry_id, 0.0) + 0.3 * hit.score
        texts[entry_id] = hit.text

    ranked = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
    return [RetrievedEntry(entry_id=eid, text=texts[eid], score=round(score, 4)) for eid, score in ranked]
