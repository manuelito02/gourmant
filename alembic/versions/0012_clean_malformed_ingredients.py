"""clean malformed and duplicate ingredients from the demo seed

Revision ID: 0012
Revises: 0011
Create Date: 2026-05-16 00:00:00.000000

The demo scraper captured recipe instructions as ingredient names (e.g.
"1/2 bâton de citronnelle", "à 15 tomates cerises") and created plural/
singular duplicates ("tomates"/"tomate"). This migration:

1. Renames duplicate plural names to their singular canonical form in place.
2. Creates clean canonical ingredients for malformed entries, re-points the
   recipes that reference them, then deletes the malformed rows.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012"
down_revision: str | Sequence[str] | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Simple rename: update name (and matching FR translation) in place.
# (old_name, new_name)
RENAMES: list[tuple[str, str]] = [
    ("tomates", "tomate"),
    ("concentré de tomates", "concentré de tomate"),
]

# Malformed → canonical mapping.
# For each malformed name: find or create the canonical ingredient, re-point
# recipe_ingredients, then delete the malformed ingredient + its translations.
# (malformed_name, canonical_name, classification, [(lang, translation)])
# Pass an empty translations list when the canonical already exists after RENAMES.
REPLACEMENTS: list[tuple[str, str, str, list[tuple[str, str]]]] = [
    (
        "1/2 bâton de citronnelle",
        "citronnelle",
        "vegan",
        [("fr", "citronnelle")],
    ),
    (
        "CS de pesto",
        "pesto",
        "vegan",
        [("fr", "pesto")],
    ),
    (
        "rases de pesto rouge",
        "pesto rouge",
        "vegan",
        [("fr", "pesto rouge")],
    ),
    (
        "à 15 tomates cerises",
        "tomates cerises",
        "vegan",
        [("fr", "tomates cerises")],
    ),
    (
        "Une très belle queue de lotte parée et nettoyée"
        " (compter en moyenne 200 g brut ou 150 g minimum net par personne)",
        "lotte",
        "pescatarian",
        [("fr", "lotte")],
    ),
    (
        # Same canonical as the entry above — the second malformed row merges in.
        "à 8 joues de lotte selon leur taille",
        "lotte",
        "pescatarian",
        [],  # translations already added by the previous entry
    ),
    (
        # "concentré de tomate" already exists after the RENAMES step.
        "concentré de tomate (facultatif)",
        "concentré de tomate",
        "vegan",
        [],
    ),
]


def _get_or_create(conn, name: str, classification: str, veg_type_id: int) -> int:
    row = conn.execute(
        sa.text("SELECT id FROM ingredients WHERE name = :n"), {"n": name}
    ).fetchone()
    if row:
        return row[0]
    return conn.execute(
        sa.text(
            "INSERT INTO ingredients (name, type_id, classification)"
            " VALUES (:n, :t, :c) RETURNING id"
        ),
        {"n": name, "t": veg_type_id, "c": classification},
    ).scalar()


def upgrade() -> None:
    conn = op.get_bind()

    veg_type_id = conn.execute(
        sa.text("SELECT id FROM ingredient_types WHERE name = 'Vegetable'")
    ).scalar()

    # 1. In-place renames
    for old, new in RENAMES:
        conn.execute(
            sa.text("UPDATE ingredients SET name = :new WHERE name = :old"),
            {"new": new, "old": old},
        )
        # Keep the FR translation in sync (demo seed mirrors name → FR translation).
        conn.execute(
            sa.text(
                "UPDATE ingredient_translations SET name = :new WHERE name = :old AND lang = 'fr'"
            ),
            {"new": new, "old": old},
        )
        print(f"  [0012] renamed '{old}' → '{new}'")

    # 2. Create canonicals, re-point, delete malformed
    for malformed, canonical, classification, translations in REPLACEMENTS:
        malformed_row = conn.execute(
            sa.text("SELECT id FROM ingredients WHERE name = :n"), {"n": malformed}
        ).fetchone()
        if not malformed_row:
            continue  # already cleaned up
        malformed_id = malformed_row[0]

        canonical_id = _get_or_create(conn, canonical, classification, veg_type_id)

        for lang, translation in translations:
            conn.execute(
                sa.text(
                    "INSERT INTO ingredient_translations (ingredient_id, lang, name)"
                    " VALUES (:id, :lang, :name) ON CONFLICT DO NOTHING"
                ),
                {"id": canonical_id, "lang": lang, "name": translation},
            )

        conn.execute(
            sa.text(
                "UPDATE recipe_ingredients SET ingredient_id = :good WHERE ingredient_id = :bad"
            ),
            {"good": canonical_id, "bad": malformed_id},
        )
        conn.execute(
            sa.text("DELETE FROM ingredient_translations WHERE ingredient_id = :id"),
            {"id": malformed_id},
        )
        conn.execute(
            sa.text("DELETE FROM ingredients WHERE id = :id"),
            {"id": malformed_id},
        )
        print(f"  [0012] '{malformed}' → '{canonical}'")


def downgrade() -> None:
    pass  # data-only cleanup; not worth reversing
