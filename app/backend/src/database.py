from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before use (handles stale connections)
    pool_size=5,  # Maintain 5 connections in pool
    max_overflow=10,  # Allow up to 10 additional connections under load
    pool_recycle=1800,  # Recycle connections after 30 minutes (Cloud SQL recommendation)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
