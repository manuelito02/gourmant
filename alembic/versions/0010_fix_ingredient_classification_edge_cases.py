"""fix ingredient classification edge cases (ligatures, missing cuts and fish names)

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-16 00:00:00.000000

Migration 0009 missed two categories of ingredients:
1. Names containing the œ ligature (e.g. "paleron de bœuf") — the keyword "boeuf"
   doesn't substring-match "bœuf" because œ ≠ oe in Unicode. The vegetarian keyword
   "oeuf" (egg) also happens to be a suffix of "boeuf"/"bœuf", causing false positives.
2. Fish names not in the 0009 keyword list (turbot, lieu noir, etc.) and common beef
   cuts (paleron, macreuse, contre filet, etc.) that don't contain the base meat word.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010"
down_revision: str | Sequence[str] | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (keyword, classification) — applied against REPLACE(LOWER(name), 'œ', 'oe').
# Checked in order; first match wins.
_EXTRA_RULES: list[tuple[str, str]] = [
    # Beef cuts that don't contain "boeuf" or other caught meat words
    ("paleron", "meat"),
    ("macreuse", "meat"),
    ("gite", "meat"),          # gîte normalized
    ("contre filet", "meat"),
    ("contre-filet", "meat"),
    ("entrecote", "meat"),     # entrecôte normalized
    ("faux-filet", "meat"),
    ("rumsteck", "meat"),
    ("filet mignon", "meat"),
    # Fish not in 0009
    ("turbot", "pescatarian"),
    ("lieu noir", "pescatarian"),
    ("lieu jaune", "pescatarian"),
    ("saint-pierre", "pescatarian"),
    ("daurade", "pescatarian"),
    ("rouget", "pescatarian"),
    ("merou", "pescatarian"),   # mérou normalized
    ("halibut", "pescatarian"),
    ("flétan", "pescatarian"),
    ("limande", "pescatarian"),
    ("carrelet", "pescatarian"),
    ("raie", "pescatarian"),
    ("merlan", "pescatarian"),
    # "bar" (sea bass) — use " bar " or "bar " to avoid matching e.g. "barbecue"
    ("bar de ligne", "pescatarian"),
    ("bar d'", "pescatarian"),
    ("filet de bar", "pescatarian"),
    ("pavés de bar", "pescatarian"),
    # Fix false-positive vegetarian: "boeuf"/"bœuf" was caught by the "oeuf" keyword
    # in 0009. Re-classify any ingredient now wrongly marked vegetarian.
    ("boeuf", "meat"),
]


def upgrade() -> None:
    conn = op.get_bind()
    other_type_row = conn.execute(
        sa.text("SELECT id FROM ingredient_types WHERE name = 'Other'")
    ).fetchone()
    if not other_type_row:
        return
    other_type_id = other_type_row[0]

    # Fetch all Other-type ingredients (vegan OR vegetarian may be wrong).
    rows = conn.execute(
        sa.text(
            "SELECT id, REPLACE(REPLACE(LOWER(name), 'œ', 'oe'), 'î', 'i') as normalized"
            " FROM ingredients WHERE type_id = :tid"
        ),
        {"tid": other_type_id},
    ).fetchall()

    updates: dict[str, list[int]] = {"meat": [], "pescatarian": [], "vegetarian": []}
    for row in rows:
        ing_id, normalized = row
        for keyword, cls in _EXTRA_RULES:
            if keyword in normalized:
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
            print(f"  [0010] reclassified {len(ids)} ingredients → {cls}")


def downgrade() -> None:
    pass  # Not worth reversing — 0009 downgrade handles the full reset
