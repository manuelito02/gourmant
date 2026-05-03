import os
import tempfile

# Must be set before app modules are imported — Pydantic reads env at Settings() init time.
os.environ.setdefault("ADMIN_EMAIL", "admin@gourmant.test")
os.environ.setdefault("ADMIN_PASSWORD", "test-admin-change-me-99")

# Redirect uploads to a temp directory so tests never touch /app/uploads.
_tmp_uploads = tempfile.mkdtemp()
os.environ.setdefault("UPLOADS_DIR", _tmp_uploads)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.config import settings as app_settings  # noqa: E402
from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.ingredient import AmountUnit, Ingredient, IngredientType  # noqa: E402
from app.models.recipe import RecipeType  # noqa: E402
from app.scripts.seed_admin import run_with_conn as seed_admin  # noqa: E402

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


@pytest.fixture(scope="session")
def tmp_uploads_dir():
    """Return the temp uploads directory used by the test session."""
    return _tmp_uploads


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


def _clean_dynamic_data(conn, seeded_ingredient_max_id: int) -> None:
    """Remove all user-created data, preserving seeded reference data, then re-seed admin."""
    conn.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
    conn.execute(
        text("DELETE FROM ingredient_translations WHERE ingredient_id > :max_id"),
        {"max_id": seeded_ingredient_max_id},
    )
    conn.execute(
        text("DELETE FROM ingredients WHERE id > :max_id"),
        {"max_id": seeded_ingredient_max_id},
    )
    seed_admin(conn)


@pytest.fixture
def db(test_engine, seeded_ingredient_max_id):
    # Clean before each test so migration-seeded demo users don't interfere.
    with test_engine.begin() as conn:
        _clean_dynamic_data(conn, seeded_ingredient_max_id)
    make_session = sessionmaker(test_engine)
    session = make_session()
    yield session
    session.close()
    with test_engine.begin() as conn:
        _clean_dynamic_data(conn, seeded_ingredient_max_id)


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


@pytest.fixture
def admin_client(client):
    """A client logged in as the seeded admin user."""
    client.post(
        "/login",
        data={"email": app_settings.admin_email, "password": app_settings.admin_password},
    )
    return client


@pytest.fixture
def ref(db):
    """IDs for seeded reference data needed to build valid payloads."""
    return {
        "type_id": db.query(RecipeType).first().id,
        "ing_type_id": db.query(IngredientType).first().id,
        "unit_id": db.query(AmountUnit).first().id,
        "ingredient_id": db.query(Ingredient).first().id,
        "ingredient_id2": db.query(Ingredient).order_by(Ingredient.id.desc()).first().id,
    }
