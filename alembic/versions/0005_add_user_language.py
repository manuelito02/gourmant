"""add language to users

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("language", sa.String(2), nullable=False, server_default="en"))


def downgrade() -> None:
    op.drop_column("users", "language")
