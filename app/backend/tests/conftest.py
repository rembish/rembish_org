"""Test fixtures for the backend test suite.

Uses SQLite in-memory database for fast, isolated tests.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth.session import get_admin_user
from src.database import Base, get_db
from src.main import app
from src.models import User


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def admin_user(db_session: Session) -> User:
    """Create and return a mock admin user."""
    user = User(
        email="admin@test.com",
        name="Test Admin",
        nickname="admin",
        is_admin=True,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Test client with database dependency override (no auth)."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_client(
    db_session: Session, admin_user: User
) -> Generator[TestClient, None, None]:
    """Test client with database and admin auth overrides."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_admin_user() -> User:
        return admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_admin_user] = override_get_admin_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
