"""reclassify demo ingredients in Other type by French keyword matching

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-16 00:00:00.000000

Migration 0008 only backfilled ingredients that were seeded at DB creation time
(in migration 0001) and whose type was known (Meat, Fish, Dairy, etc.). The demo
recipe seed script (seed_demo_recipes.py) creates French-named ingredients with
type "Other", so they all defaulted to "vegan". This migration re-classifies
every ingredient in the "Other" type using keyword matching on the ingredient name.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009"
down_revision: str | Sequence[str] | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Keyword → classification pairs checked in order (meat first, most specific wins).
# Each tuple is (keyword_substring, classification).
_RULES: list[tuple[str, str]] = [
    # Meat
    ("poulet", "meat"),
    ("volaille", "meat"),
    ("canard", "meat"),
    ("magret", "meat"),
    ("agneau", "meat"),
    ("mouton", "meat"),
    ("porc", "meat"),
    ("boeuf", "meat"),
    ("veau", "meat"),
    ("lapin", "meat"),
    ("dinde", "meat"),
    ("pintade", "meat"),
    ("caille", "meat"),
    ("faisan", "meat"),
    ("gibier", "meat"),
    ("chevreuil", "meat"),
    ("sanglier", "meat"),
    ("lardons", "meat"),
    ("lard", "meat"),
    ("jambon", "meat"),
    ("bacon", "meat"),
    ("saucisse", "meat"),
    ("saucisson", "meat"),
    ("merguez", "meat"),
    ("andouille", "meat"),
    ("viande", "meat"),
    ("haché", "meat"),
    ("bouillon de boeuf", "meat"),
    ("bouillon de volaille", "meat"),
    ("bouillon volaille", "meat"),
    ("fond de veau", "meat"),
    ("fond blanc", "meat"),
    ("fond brun", "meat"),
    ("foie", "meat"),
    ("rognon", "meat"),
    ("gésier", "meat"),
    ("abat", "meat"),
    # Pescatarian
    ("saumon", "pescatarian"),
    ("thon", "pescatarian"),
    ("cabillaud", "pescatarian"),
    ("sole", "pescatarian"),
    ("truite", "pescatarian"),
    ("dorade", "pescatarian"),
    ("lotte", "pescatarian"),
    ("merlu", "pescatarian"),
    ("morue", "pescatarian"),
    ("maquereau", "pescatarian"),
    ("anchois", "pescatarian"),
    ("sardine", "pescatarian"),
    ("hareng", "pescatarian"),
    ("perche", "pescatarian"),
    ("brochet", "pescatarian"),
    ("sandre", "pescatarian"),
    ("crevette", "pescatarian"),
    ("homard", "pescatarian"),
    ("langouste", "pescatarian"),
    ("langoustine", "pescatarian"),
    ("calamar", "pescatarian"),
    ("calmar", "pescatarian"),
    ("poulpe", "pescatarian"),
    ("moule", "pescatarian"),
    ("palourde", "pescatarian"),
    ("huître", "pescatarian"),
    ("crabe", "pescatarian"),
    ("coquille", "pescatarian"),
    ("saint-jacques", "pescatarian"),
    ("seiche", "pescatarian"),
    ("oursin", "pescatarian"),
    ("bulot", "pescatarian"),
    ("bigorneaux", "pescatarian"),
    ("fumet de poisson", "pescatarian"),
    ("fumet de crustacé", "pescatarian"),
    ("fond de poisson", "pescatarian"),
    # Vegetarian
    ("crème fraîche", "vegetarian"),
    ("crème liquide", "vegetarian"),
    ("crème entière", "vegetarian"),
    ("crème double", "vegetarian"),
    ("crème", "vegetarian"),
    ("beurre", "vegetarian"),
    ("fromage", "vegetarian"),
    ("gruyère", "vegetarian"),
    ("comté", "vegetarian"),
    ("emmental", "vegetarian"),
    ("parmesan", "vegetarian"),
    ("mozzarella", "vegetarian"),
    ("roquefort", "vegetarian"),
    ("camembert", "vegetarian"),
    ("brie", "vegetarian"),
    ("cheddar", "vegetarian"),
    ("reblochon", "vegetarian"),
    ("raclette", "vegetarian"),
    ("beaufort", "vegetarian"),
    ("chèvre", "vegetarian"),
    ("ricotta", "vegetarian"),
    ("mascarpone", "vegetarian"),
    ("feta", "vegetarian"),
    ("gouda", "vegetarian"),
    ("édam", "vegetarian"),
    ("lait", "vegetarian"),
    ("yaourt", "vegetarian"),
    ("fromage blanc", "vegetarian"),
    ("œuf", "vegetarian"),
    ("oeuf", "vegetarian"),
    ("jaune d", "vegetarian"),
    ("blanc d", "vegetarian"),
]


def upgrade() -> None:
    conn = op.get_bind()
    other_type_row = conn.execute(
        sa.text("SELECT id FROM ingredient_types WHERE name = 'Other'")
    ).fetchone()
    if not other_type_row:
        return
    other_type_id = other_type_row[0]

    # Fetch all ingredients in the Other type that are currently classified as vegan.
    rows = conn.execute(
        sa.text(
            "SELECT id, LOWER(name) as lname FROM ingredients"
            " WHERE type_id = :tid AND classification = 'vegan'"
        ),
        {"tid": other_type_id},
    ).fetchall()

    updates: dict[str, list[int]] = {"meat": [], "pescatarian": [], "vegetarian": []}
    for row in rows:
        ing_id, lname = row
        for keyword, cls in _RULES:
            if keyword in lname:
                updates[cls].append(ing_id)
                break

    for cls, ids in updates.items():
        if ids:
            conn.execute(
                sa.text(
                    "UPDATE ingredients SET classification = :cls WHERE id = ANY(:ids)"
                ),
                {"cls": cls, "ids": ids},
            )
            print(f"  [0009] reclassified {len(ids)} ingredients → {cls}")


def downgrade() -> None:
    conn = op.get_bind()
    other_type_row = conn.execute(
        sa.text("SELECT id FROM ingredient_types WHERE name = 'Other'")
    ).fetchone()
    if not other_type_row:
        return
    # Reset all Other-type ingredients back to vegan (reversing is imprecise but safe).
    conn.execute(
        sa.text(
            "UPDATE ingredients SET classification = 'vegan'"
            " WHERE type_id = :tid"
        ),
        {"tid": other_type_row[0]},
    )
