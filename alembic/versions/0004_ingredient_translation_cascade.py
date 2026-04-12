"""Add ON DELETE CASCADE to ingredient_translations.ingredient_id FK

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-12 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Explicit name so upgrade/downgrade are symmetric.
_NEW_FK = "fk_ingredient_translations_ingredient_id_cascade"


def upgrade() -> None:
    op.drop_constraint(
        "ingredient_translations_ingredient_id_fkey",
        "ingredient_translations",
        type_="foreignkey",
    )
    op.create_foreign_key(
        _NEW_FK,
        "ingredient_translations",
        "ingredients",
        ["ingredient_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(_NEW_FK, "ingredient_translations", type_="foreignkey")
    op.create_foreign_key(
        "ingredient_translations_ingredient_id_fkey",
        "ingredient_translations",
        "ingredients",
        ["ingredient_id"],
        ["id"],
    )
