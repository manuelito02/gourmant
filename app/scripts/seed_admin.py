"""Idempotently create or promote the configured admin user.

Called from entrypoint.sh after `alembic upgrade head`. Safe to run multiple times:
  - If no user with ADMIN_EMAIL exists: creates one with ADMIN_PASSWORD and role=admin.
  - If user exists but role != admin: promotes to admin (does not touch password).
  - If user exists with role=admin: no-op.
"""

from sqlalchemy import create_engine, text

from app.config import settings
from app.routers.auth import hash_password


def run_with_conn(conn) -> None:
    row = conn.execute(
        text("SELECT id, role FROM users WHERE email = :email"),
        {"email": settings.admin_email.lower()},
    ).fetchone()

    if row is None:
        hashed = hash_password(settings.admin_password)
        conn.execute(
            text(
                "INSERT INTO users (email, first_name, last_name, hashed_password, language, role)"
                " VALUES (:email, 'Admin', 'User', :pw, 'en', 'admin')"
            ),
            {"email": settings.admin_email.lower(), "pw": hashed},
        )
        print(f"[seed_admin] Created admin user: {settings.admin_email}")
    elif row.role != "admin":
        conn.execute(
            text("UPDATE users SET role = 'admin' WHERE id = :id"),
            {"id": row.id},
        )
        print(f"[seed_admin] Promoted existing user to admin: {settings.admin_email}")
    else:
        print(f"[seed_admin] Admin user already exists: {settings.admin_email}")


def run() -> None:
    engine = create_engine(settings.database_url)
    with engine.begin() as conn:
        run_with_conn(conn)
    engine.dispose()


if __name__ == "__main__":
    run()
