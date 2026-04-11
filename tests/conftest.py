import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

_BASE_URL = "postgresql+psycopg://gourmant:gourmant@localhost:5432"
_TEST_DB_NAME = "gourmant_test"
TEST_DATABASE_URL = f"{_BASE_URL}/{_TEST_DB_NAME}"


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # Create the test database if it doesn't exist
    engine = create_engine(f"{_BASE_URL}/gourmant", isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": _TEST_DB_NAME},
        ).fetchone()
        if not exists:
            conn.execute(text(f"CREATE DATABASE {_TEST_DB_NAME}"))
    engine.dispose()

    # Create all tables
    test_engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(test_engine)
    test_engine.dispose()


@pytest.fixture(scope="session")
def test_engine(setup_test_database):
    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def db(test_engine):
    make_session = sessionmaker(test_engine)
    session = make_session()
    yield session
    session.close()
    with test_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
