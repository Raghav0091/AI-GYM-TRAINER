from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine_kwargs = {"pool_pre_ping": True}

if settings.database_url.startswith("postgresql"):
    engine_kwargs["connect_args"] = {"connect_timeout": 3}

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models so SQLAlchemy registers tables before create_all.
    from app.models import room, user, workout  # noqa: F401

    Base.metadata.create_all(bind=engine)
