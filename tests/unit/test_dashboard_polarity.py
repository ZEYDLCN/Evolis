from src.analytics.dashboard import _weekly_evolution
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.base import Base
from src.database.models import User
import datetime as dt


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_zero_change_is_neutral_not_negative():
    """Regression: a flat week used to render context-switching as a
    regression (red) just because (0 >= 0) == False for a lower-is-better
    metric. No change should never be colored as bad."""
    db = _make_session()
    user = User(email="a@b.com", hashed_password="x")
    db.add(user)
    db.commit()

    rows = _weekly_evolution(db, user.id, dt.datetime(2026, 8, 23))
    for row in rows:
        assert row["is_positive"] is None
