import datetime as dt

from cryptography.fernet import Fernet
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.database.base import Base
from src.database.models import Entry, User
from src.rag.retriever import keyword_search


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def test_raw_text_is_ciphertext_on_disk_but_plaintext_through_the_orm(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    engine, db = _make_session()

    user = User(email="enc@test.com", hashed_password="x")
    db.add(user)
    db.flush()
    entry = Entry(user_id=user.id, raw_text="Bugün Docker ile uğraştım.", entry_date=dt.datetime.utcnow())
    db.add(entry)
    db.commit()

    # Through the ORM: transparently decrypted.
    reloaded = db.get(Entry, entry.id)
    assert reloaded.raw_text == "Bugün Docker ile uğraştım."

    # On disk: not plaintext. Plain text() bypasses the EncryptedText type
    # decorator entirely (a Core select() against the typed column would
    # still run it and silently decrypt) — this is the only way to see what
    # SQLite actually stored.
    with engine.connect() as conn:
        raw_value = conn.execute(text("SELECT raw_text FROM entries")).scalar()
    assert raw_value != "Bugün Docker ile uğraştım."
    assert "Docker" not in raw_value


def test_keyword_search_works_in_encrypted_mode(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    _, db = _make_session()

    user = User(email="enc2@test.com", hashed_password="x")
    db.add(user)
    db.flush()
    db.add(Entry(user_id=user.id, raw_text="RAG pipeline geliştirdim.", entry_date=dt.datetime.utcnow()))
    db.add(Entry(user_id=user.id, raw_text="Frontend UI çalıştım.", entry_date=dt.datetime.utcnow()))
    db.commit()

    results = keyword_search(db, user.id, "RAG")
    assert len(results) == 1
    assert "RAG" in results[0].text
