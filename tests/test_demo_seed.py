"""Tests for the demo recipe seed script."""

from sqlalchemy import text

from app.routers.auth import hash_password
from app.scripts.seed_demo_recipes import BOB_EMAIL, CHARLY_EMAIL, run_with_conn


def _seed_bob_charly(conn) -> None:
    """Insert bob and charly so the seed script can find them."""
    for email, first, last in [
        (BOB_EMAIL, "Bob", "Martin"),
        (CHARLY_EMAIL, "Charly", "Dupont"),
    ]:
        pw = hash_password("test-password-42")
        conn.execute(
            text(
                "INSERT INTO users (email, first_name, last_name, hashed_password)"
                " VALUES (:e, :f, :l, :p) ON CONFLICT DO NOTHING"
            ),
            {"e": email, "f": first, "l": last, "p": pw},
        )


def test_seed_inserts_50_recipes(test_engine, tmp_uploads_dir, seeded_ingredient_max_id):
    with test_engine.begin() as conn:
        from tests.conftest import _clean_dynamic_data

        _clean_dynamic_data(conn, seeded_ingredient_max_id)
        _seed_bob_charly(conn)

    with test_engine.begin() as conn:
        # Patch UPLOADS_DIR so images are written to the test temp dir
        import app.scripts.seed_demo_recipes as mod

        original = mod.UPLOADS_DIR
        mod.UPLOADS_DIR = __import__("pathlib").Path(tmp_uploads_dir)
        try:
            run_with_conn(conn)
        finally:
            mod.UPLOADS_DIR = original

    with test_engine.connect() as conn:
        total = conn.execute(
            text(
                "SELECT COUNT(*) FROM recipes r"
                " JOIN users u ON r.user_id = u.id"
                " WHERE u.email IN (:bob, :charly)"
            ),
            {"bob": BOB_EMAIL, "charly": CHARLY_EMAIL},
        ).scalar()
        assert total == 50, f"Expected 50 recipes, got {total}"

        bob_count = conn.execute(
            text(
                "SELECT COUNT(*) FROM recipes r JOIN users u ON r.user_id = u.id WHERE u.email = :e"
            ),
            {"e": BOB_EMAIL},
        ).scalar()
        charly_count = conn.execute(
            text(
                "SELECT COUNT(*) FROM recipes r JOIN users u ON r.user_id = u.id WHERE u.email = :e"
            ),
            {"e": CHARLY_EMAIL},
        ).scalar()
        # With Random(42) and 50 recipes, each user should get a reasonable share
        assert bob_count >= 15, f"Bob has only {bob_count} recipes"
        assert charly_count >= 15, f"Charly has only {charly_count} recipes"


def test_seed_is_idempotent(test_engine, tmp_uploads_dir, seeded_ingredient_max_id):
    with test_engine.begin() as conn:
        from tests.conftest import _clean_dynamic_data

        _clean_dynamic_data(conn, seeded_ingredient_max_id)
        _seed_bob_charly(conn)

    import app.scripts.seed_demo_recipes as mod

    original = mod.UPLOADS_DIR
    mod.UPLOADS_DIR = __import__("pathlib").Path(tmp_uploads_dir)
    try:
        with test_engine.begin() as conn:
            run_with_conn(conn)
        with test_engine.begin() as conn:
            run_with_conn(conn)  # second call must be a no-op
    finally:
        mod.UPLOADS_DIR = original

    with test_engine.connect() as conn:
        total = conn.execute(
            text(
                "SELECT COUNT(*) FROM recipes r"
                " JOIN users u ON r.user_id = u.id"
                " WHERE u.email IN (:bob, :charly)"
            ),
            {"bob": BOB_EMAIL, "charly": CHARLY_EMAIL},
        ).scalar()
        assert total == 50, f"Idempotency failed: got {total} recipes after 2 runs"
