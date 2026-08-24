from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.base import Base
from src.database.models import Entry, EntryTopic, ExtractionFeedback, User
from src.services.entry_service import correct_entry_extraction


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_correct_entry_updates_topics_and_status_and_records_feedback():
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.flush()

    entry = Entry(
        user_id=user.id,
        raw_text="LangGraph çalıştım.",
        completion_status="partial",
        extraction_raw={"topics": ["LnagGraph"], "completion_status": "partial"},
    )
    db.add(entry)
    db.flush()
    db.add(EntryTopic(entry_id=entry.id, topic="LnagGraph"))
    db.commit()

    corrected = correct_entry_extraction(
        db, user.id, entry.id, {"topics": ["LangGraph"], "completion_status": "done"}
    )

    assert corrected.completion_status == "done"
    assert corrected.extraction_raw["topics"] == ["LangGraph"]

    feedback = db.query(ExtractionFeedback).filter(ExtractionFeedback.entry_id == entry.id).first()
    assert feedback is not None
    assert feedback.original_extraction["topics"] == ["LnagGraph"]
    assert feedback.corrected_extraction["topics"] == ["LangGraph"]


def test_correct_entry_returns_none_for_wrong_user():
    db = _make_session()
    owner = User(email="a@b.com", hashed_password="x")
    other = User(email="c@d.com", hashed_password="x")
    db.add_all([owner, other])
    db.flush()
    entry = Entry(user_id=owner.id, raw_text="x")
    db.add(entry)
    db.commit()

    result = correct_entry_extraction(db, other.id, entry.id, {"completion_status": "done"})
    assert result is None
