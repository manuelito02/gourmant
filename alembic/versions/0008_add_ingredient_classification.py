"""add ingredient dietary classification

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-16 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008"
down_revision: str | Sequence[str] | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Ingredient-type → classification (covers the bulk of seeded ingredients).
# Values declared in ascending diet order (vegan < vegetarian < pescatarian < meat)
# so that PostgreSQL MAX() returns the correct "highest wins" value.
TYPE_DEFAULT: dict[str, str] = {
    "Meat": "meat",
    "Fish": "pescatarian",
    "Seafood": "pescatarian",
    "Dairy": "vegetarian",
    "Egg": "vegetarian",
    # All remaining types default to vegan (Vegetable, Fruit, Grain, Legume,
    # Nut, Spice, Herb, Oil, Sweetener, Condiment, Beverage, Other).
}

# Per-ingredient overrides for items whose type default would be wrong.
OVERRIDES: dict[str, str] = {
    "honey": "vegetarian",           # animal product despite Sweetener type
    "mayonnaise": "vegetarian",      # contains egg despite Condiment type
    "worcestershire sauce": "pescatarian",  # traditionally contains anchovies
    "fish sauce": "pescatarian",
    "oyster sauce": "pescatarian",
    "chicken stock": "meat",
    "beef stock": "meat",
    "gelatin": "meat",               # derived from animal collagen
}


def upgrade() -> None:
    op.execute(
        "CREATE TYPE dietclassification AS ENUM ('vegan', 'vegetarian', 'pescatarian', 'meat')"
    )
    op.add_column(
        "ingredients",
        sa.Column(
            "classification",
            sa.Enum("vegan", "vegetarian", "pescatarian", "meat", name="dietclassification", create_type=False),
            nullable=False,
            server_default="vegan",
        ),
    )

    conn = op.get_bind()

    # Bulk-update by ingredient type using the TYPE_DEFAULT mapping.
    for type_name, classification in TYPE_DEFAULT.items():
        conn.execute(
            sa.text(
                "UPDATE ingredients SET classification = :cls "
                "WHERE type_id = (SELECT id FROM ingredient_types WHERE name = :type_name)"
            ),
            {"cls": classification, "type_name": type_name},
        )

    # Apply per-ingredient overrides.
    for ing_name, classification in OVERRIDES.items():
        conn.execute(
            sa.text("UPDATE ingredients SET classification = :cls WHERE name = :name"),
            {"cls": classification, "name": ing_name},
        )


def downgrade() -> None:
    op.drop_column("ingredients", "classification")
    op.execute("DROP TYPE dietclassification")
