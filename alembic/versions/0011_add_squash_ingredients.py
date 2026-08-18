"""add squash/pumpkin ingredient varieties and fix malformed butternut ingredient

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-16 00:00:00.000000

Adds 9 squash/pumpkin varieties to the ingredient table with FR/DE/NL translations.
Also replaces the malformed demo ingredient
"environ de chair de courge butternut. épluchée et découpée en cubes de 1.5 cm"
(a recipe instruction, not an ingredient name) with the proper "butternut squash"
entry, and re-points the one recipe that referenced it.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011"
down_revision: str | Sequence[str] | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (english_name, [(lang, translation), ...])
SQUASHES: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "butternut squash",
        [("fr", "courge butternut"), ("de", "Butternusskürbis"), ("nl", "butternutpompoen")],
    ),
    (
        "acorn squash",
        [("fr", "courge poivrée"), ("de", "Eichelkürbis"), ("nl", "eierpompoen")],
    ),
    (
        "kabocha squash",
        [("fr", "kabocha"), ("de", "Kabocha-Kürbis"), ("nl", "kabocha")],
    ),
    (
        "Hokkaido pumpkin",
        [("fr", "Hokkaido"), ("de", "Hokkaido-Kürbis"), ("nl", "Hokkaidopompoen")],
    ),
    (
        "spaghetti squash",
        [("fr", "courge spaghetti"), ("de", "Spaghettikürbis"), ("nl", "spaghettipompoen")],
    ),
    (
        "potimarron",
        [("fr", "potimarron"), ("de", "Potimarron"), ("nl", "potimarron")],
    ),
    (
        "carat squash",
        [("fr", "carat"), ("de", "Carat-Kürbis"), ("nl", "caraatpompoen")],
    ),
    (
        "bleu de Hongrie squash",
        [
            ("fr", "bleu de Hongrie"),
            ("de", "Blauer Ungarischer Kürbis"),
            ("nl", "Hongaarse blauwe pompoen"),
        ],
    ),
    (
        "delicata squash",
        [("fr", "delicata"), ("de", "Delicata-Kürbis"), ("nl", "delicata")],
    ),
]

MALFORMED_NAME = "environ de chair de courge butternut. épluchée et découpée en cubes de 1.5 cm"


def upgrade() -> None:
    conn = op.get_bind()

    veg_type = conn.execute(
        sa.text("SELECT id FROM ingredient_types WHERE name = 'Vegetable'")
    ).scalar()

    # Insert each squash variety, skip if already present.
    for eng_name, translations in SQUASHES:
        existing = conn.execute(
            sa.text("SELECT id FROM ingredients WHERE name = :n"), {"n": eng_name}
        ).scalar()
        if existing:
            ing_id = existing
        else:
            ing_id = conn.execute(
                sa.text(
                    "INSERT INTO ingredients (name, type_id, classification)"
                    " VALUES (:n, :t, 'vegan') RETURNING id"
                ),
                {"n": eng_name, "t": veg_type},
            ).scalar()

        for lang, translation in translations:
            conn.execute(
                sa.text(
                    "INSERT INTO ingredient_translations (ingredient_id, lang, name)"
                    " VALUES (:id, :lang, :name) ON CONFLICT DO NOTHING"
                ),
                {"id": ing_id, "lang": lang, "name": translation},
            )

    # Replace the malformed butternut ingredient with "butternut squash".
    bad_row = conn.execute(
        sa.text("SELECT id FROM ingredients WHERE name = :n"), {"n": MALFORMED_NAME}
    ).fetchone()
    if bad_row:
        bad_id = bad_row[0]
        good_id = conn.execute(
            sa.text("SELECT id FROM ingredients WHERE name = 'butternut squash'")
        ).scalar()
        # Re-point recipe_ingredients rows.
        conn.execute(
            sa.text(
                "UPDATE recipe_ingredients SET ingredient_id = :good WHERE ingredient_id = :bad"
            ),
            {"good": good_id, "bad": bad_id},
        )
        # Remove the malformed ingredient and its translations.
        conn.execute(
            sa.text("DELETE FROM ingredient_translations WHERE ingredient_id = :id"),
            {"id": bad_id},
        )
        conn.execute(
            sa.text("DELETE FROM ingredients WHERE id = :id"),
            {"id": bad_id},
        )
        print(f"  [0011] replaced ingredient {bad_id!r} with 'butternut squash' (id={good_id})")

    print(f"  [0011] added/verified {len(SQUASHES)} squash varieties")


def downgrade() -> None:
    conn = op.get_bind()
    for eng_name, _ in SQUASHES:
        row = conn.execute(
            sa.text("SELECT id FROM ingredients WHERE name = :n"), {"n": eng_name}
        ).fetchone()
        if row:
            conn.execute(
                sa.text("DELETE FROM ingredient_translations WHERE ingredient_id = :id"),
                {"id": row[0]},
            )
            conn.execute(sa.text("DELETE FROM ingredients WHERE id = :id"), {"id": row[0]})
