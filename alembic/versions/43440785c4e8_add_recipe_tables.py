"""add recipe tables

Revision ID: 43440785c4e8
Revises: a85ddaa432c6
Create Date: 2026-04-11 17:22:44.955656

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "43440785c4e8"
down_revision: str | Sequence[str] | None = "a85ddaa432c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INGREDIENT_TYPES = [
    "Vegetable",
    "Fruit",
    "Meat",
    "Fish",
    "Seafood",
    "Dairy",
    "Egg",
    "Grain",
    "Legume",
    "Nut",
    "Spice",
    "Herb",
    "Oil",
    "Sweetener",
    "Condiment",
    "Beverage",
    "Other",
]

AMOUNT_UNITS = [
    ("gram", "g"),
    ("kilogram", "kg"),
    ("milliliter", "ml"),
    ("liter", "L"),
    ("teaspoon", "tsp"),
    ("tablespoon", "tbsp"),
    ("cup", "cup"),
    ("piece", "pc"),
    ("pinch", "pinch"),
    ("to taste", "to taste"),
]

RECIPE_TYPES = [
    "Starter",
    "Main course",
    "Dessert",
    "Sauce",
    "Side dish",
    "Soup",
    "Salad",
    "Breakfast",
    "Snack",
    "Beverage",
]


def upgrade() -> None:
    # ── Reference tables ──────────────────────────────────────────────────────
    ingredient_types = op.create_table(
        "ingredient_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.bulk_insert(ingredient_types, [{"name": n} for n in INGREDIENT_TYPES])

    amount_units = op.create_table(
        "amount_units",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("abbreviation", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("abbreviation"),
    )
    op.bulk_insert(amount_units, [{"name": n, "abbreviation": a} for n, a in AMOUNT_UNITS])

    recipe_types = op.create_table(
        "recipe_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.bulk_insert(recipe_types, [{"name": n} for n in RECIPE_TYPES])

    # ── Ingredient catalog ────────────────────────────────────────────────────
    op.create_table(
        "ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("type_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["type_id"], ["ingredient_types.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_ingredients_name"), "ingredients", ["name"], unique=True)

    # ── Recipes ───────────────────────────────────────────────────────────────
    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["type_id"], ["recipe_types.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recipes_user_id"), "recipes", ["user_id"], unique=False)

    # ── Recipe ↔ Ingredient join ──────────────────────────────────────────────
    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"]),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["amount_units.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── Steps ─────────────────────────────────────────────────────────────────
    op.create_table(
        "steps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recipe_id", "position", name="uq_step_recipe_position"),
    )


def downgrade() -> None:
    op.drop_table("steps")
    op.drop_table("recipe_ingredients")
    op.drop_index(op.f("ix_recipes_user_id"), table_name="recipes")
    op.drop_table("recipes")
    op.drop_index(op.f("ix_ingredients_name"), table_name="ingredients")
    op.drop_table("ingredients")
    op.drop_table("recipe_types")
    op.drop_table("amount_units")
    op.drop_table("ingredient_types")
