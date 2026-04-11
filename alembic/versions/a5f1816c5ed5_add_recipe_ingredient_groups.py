"""add recipe ingredient groups

Revision ID: a5f1816c5ed5
Revises: 43440785c4e8
Create Date: 2026-04-11 17:34:04.647215

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a5f1816c5ed5"
down_revision: str | Sequence[str] | None = "43440785c4e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recipe_ingredient_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column(
        "recipe_ingredients",
        sa.Column("group_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_recipe_ingredients_group",
        "recipe_ingredients",
        "recipe_ingredient_groups",
        ["group_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_recipe_ingredients_group", "recipe_ingredients", type_="foreignkey")
    op.drop_column("recipe_ingredients", "group_id")
    op.drop_table("recipe_ingredient_groups")
