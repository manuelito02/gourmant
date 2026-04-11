"""add centiliter and deciliter amount units

Revision ID: c4d1e2f3a5b6
Revises: b3c9d2e1f4a0
Create Date: 2026-04-11 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c4d1e2f3a5b6"
down_revision: str | Sequence[str] | None = "b3c9d2e1f4a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_UNITS = [
    ("centiliter", "cl"),
    ("deciliter", "dl"),
]


def upgrade() -> None:
    units_table = sa.table(
        "amount_units",
        sa.column("name", sa.String),
        sa.column("abbreviation", sa.String),
    )
    op.bulk_insert(units_table, [{"name": n, "abbreviation": a} for n, a in NEW_UNITS])


def downgrade() -> None:
    conn = op.get_bind()
    names = [n for n, _ in NEW_UNITS]
    conn.execute(
        sa.text("DELETE FROM amount_units WHERE name = ANY(:names)"),
        {"names": names},
    )
