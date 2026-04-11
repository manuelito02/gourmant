import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app

_BASE_URL = "postgresql+psycopg://gourmant:gourmant@localhost:5432"
_TEST_DB_NAME = "gourmant_test"
TEST_DATABASE_URL = f"{_BASE_URL}/{_TEST_DB_NAME}"

VALID_USER = {
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane@example.com",
    "password": "correct-horse-battery-staple",
    "password_confirm": "correct-horse-battery-staple",
}


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    from alembic.config import Config

    from alembic import command

    # Drop and recreate for a clean slate on every test session
    engine = create_engine(f"{_BASE_URL}/gourmant", isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {_TEST_DB_NAME} WITH (FORCE)"))
        conn.execute(text(f"CREATE DATABASE {_TEST_DB_NAME}"))
    engine.dispose()

    # Run all migrations — creates tables and seeds all reference data.
    # TEST_DATABASE_URL env var is read by alembic/env.py to override the app DB URL.
    os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL
    try:
        command.upgrade(Config("alembic.ini"), "head")
    finally:
        del os.environ["TEST_DATABASE_URL"]


@pytest.fixture(scope="session")
def test_engine(setup_test_database):
    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def seeded_ingredient_max_id(test_engine):
    """Highest ingredient id present after migrations — used to clean up test-created ones."""
    with test_engine.connect() as conn:
        return conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM ingredients")).scalar()


@pytest.fixture
def db(test_engine, seeded_ingredient_max_id):
    make_session = sessionmaker(test_engine)
    session = make_session()
    yield session
    session.close()
    with test_engine.begin() as conn:
        conn.execute(
            text("DELETE FROM ingredients WHERE id > :max_id"),
            {"max_id": seeded_ingredient_max_id},
        )
        conn.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    """A client that is already registered and logged in."""
    client.post("/register", data=VALID_USER)
    return client
