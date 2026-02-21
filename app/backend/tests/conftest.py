"""Test fixtures for the backend test suite.

Uses SQLite in-memory database for fast, isolated tests.
Environment variables are forced before app import to ensure
deterministic behavior regardless of local .env files.
"""

import os

# Force deterministic settings before any app imports (env vars override .env file)
os.environ["GOOGLE_CLIENT_ID"] = ""
os.environ["GOOGLE_CLIENT_SECRET"] = ""
os.environ["TELEGRAM_TOKEN"] = ""
os.environ["TELEGRAM_CHAT_ID"] = ""
os.environ["TURNSTILE_SECRET"] = ""
os.environ["INSTAGRAM_ACCOUNT_ID"] = ""
os.environ["INSTAGRAM_PAGE_TOKEN"] = ""
os.environ["AERODATABOX_API_KEY"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["VAULT_ENCRYPTION_KEY"] = ""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth.session import get_admin_user, get_trips_viewer
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
        role="admin",
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
    with TestClient(app, headers={"X-CSRF": "1"}) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_client(db_session: Session, admin_user: User) -> Generator[TestClient, None, None]:
    """Test client with database and admin auth overrides."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_admin_user() -> User:
        return admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_admin_user] = override_get_admin_user
    app.dependency_overrides[get_trips_viewer] = override_get_admin_user
    with TestClient(app, headers={"X-CSRF": "1"}) as c:
        yield c
    app.dependency_overrides.clear()
