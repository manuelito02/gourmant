"""add user role

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE TYPE userrole AS ENUM ('user', 'admin')")
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.Enum("user", "admin", name="userrole", create_type=False),
            nullable=False,
            server_default="user",
        ),
    )
    op.drop_constraint("recipes_user_id_fkey", "recipes", type_="foreignkey")
    op.create_foreign_key(
        "recipes_user_id_fkey", "recipes", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )


def downgrade() -> None:
    op.drop_constraint("recipes_user_id_fkey", "recipes", type_="foreignkey")
    op.create_foreign_key(
        "recipes_user_id_fkey", "recipes", "users", ["user_id"], ["id"]
    )
    op.drop_column("users", "role")
    op.execute("DROP TYPE userrole")
