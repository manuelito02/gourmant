"""add email first last name to users

Revision ID: a85ddaa432c6
Revises: c0cd0ec62bf2
Create Date: 2026-04-11 16:41:04.260579

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a85ddaa432c6"
down_revision: str | Sequence[str] | None = "c0cd0ec62bf2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop existing users data and username index since this is a dev schema change
    op.execute("DELETE FROM users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_column("users", "username")
    op.add_column("users", sa.Column("email", sa.String(255), nullable=False, server_default=""))
    op.add_column(
        "users", sa.Column("first_name", sa.String(100), nullable=False, server_default="")
    )
    op.add_column(
        "users", sa.Column("last_name", sa.String(100), nullable=False, server_default="")
    )
    op.alter_column("users", "email", server_default=None)
    op.alter_column("users", "first_name", server_default=None)
    op.alter_column("users", "last_name", server_default=None)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)


def downgrade() -> None:
    op.execute("DELETE FROM users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
    op.drop_column("users", "email")
    op.add_column("users", sa.Column("username", sa.String(50), nullable=False, server_default=""))
    op.alter_column("users", "username", server_default=None)
    op.create_index("ix_users_username", "users", ["username"], unique=True)
