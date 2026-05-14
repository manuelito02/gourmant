"""Seed 50 French demo recipes for bob and charly from the pre-generated dataset.

Idempotent: skips the whole run if bob+charly already have ≥ 50 recipes combined.

Usage:
  docker compose exec app python -m app.scripts.seed_demo_recipes
  # or locally (needs DATABASE_URL set):
  uv run python -m app.scripts.seed_demo_recipes
"""

import json
import os
import random
import shutil
from pathlib import Path

from sqlalchemy import create_engine, text

from app.config import settings

DATA_DIR = Path(__file__).parent / "demo_recipes"
IMAGES_SRC = DATA_DIR / "images"
UPLOADS_DIR = Path(os.environ.get("UPLOADS_DIR", "/app/uploads"))

BOB_EMAIL = "bob@example.com"
CHARLY_EMAIL = "charly@example.com"

# Map JSON type_name → canonical English DB value in recipe_types.name
# (must match the seeded values from migration 0001)
TYPE_ALIASES: dict[str, list[str]] = {
    "Main course": ["Main course", "Plat principal"],
    "Starter": ["Starter", "Entrée"],
    "Dessert": ["Dessert"],
    "Soup": ["Soup", "Soupe"],
    "Salad": ["Salad", "Salade"],
    "Sauce": ["Sauce"],
    "Side dish": ["Side dish", "Accompagnement"],
    "Breakfast": ["Breakfast", "Petit-déjeuner"],
    "Snack": ["Snack"],
    "Beverage": ["Beverage", "Boisson"],
}

# Canonical English unit name → DB name (must match AmountUnit.name)
UNIT_ALIASES: dict[str, list[str]] = {
    "gram": ["gram"],
    "kilogram": ["kilogram"],
    "milliliter": ["milliliter"],
    "liter": ["liter"],
    "centiliter": ["centiliter"],
    "deciliter": ["deciliter"],
    "teaspoon": ["teaspoon"],
    "tablespoon": ["tablespoon"],
    "cup": ["cup"],
    "piece": ["piece"],
    "pinch": ["pinch"],
    "to taste": ["to taste"],
}


def run_with_conn(conn) -> None:
    # Idempotency check
    existing = conn.execute(
        text(
            "SELECT COUNT(*) FROM recipes r"
            " JOIN users u ON r.user_id = u.id"
            " WHERE u.email IN (:bob, :charly)"
        ),
        {"bob": BOB_EMAIL, "charly": CHARLY_EMAIL},
    ).scalar()
    if existing >= 50:
        print(f"[seed_demo] Already have {existing} demo recipes — skipping.")
        return

    # Look up user IDs
    def get_user_id(email: str) -> int | None:
        row = conn.execute(text("SELECT id FROM users WHERE email = :e"), {"e": email}).fetchone()
        return row[0] if row else None

    bob_id = get_user_id(BOB_EMAIL)
    charly_id = get_user_id(CHARLY_EMAIL)
    if not bob_id or not charly_id:
        print("[seed_demo] bob or charly not found — run migrations first.")
        return

    user_ids = [bob_id, charly_id]

    # Build type lookup: name → id (try each alias)
    def get_type_id(type_name: str) -> int | None:
        aliases = TYPE_ALIASES.get(type_name, [type_name])
        for alias in aliases:
            row = conn.execute(
                text("SELECT id FROM recipe_types WHERE name = :n"), {"n": alias}
            ).fetchone()
            if row:
                return row[0]
        # Fallback: first type
        row = conn.execute(text("SELECT id FROM recipe_types LIMIT 1")).fetchone()
        return row[0] if row else None

    # Build unit lookup: canonical name → id
    def get_unit_id(unit_name: str) -> int | None:
        aliases = UNIT_ALIASES.get(unit_name, [unit_name])
        for alias in aliases:
            row = conn.execute(
                text("SELECT id FROM amount_units WHERE name = :n"), {"n": alias}
            ).fetchone()
            if row:
                return row[0]
        # Fallback: piece
        row = conn.execute(text("SELECT id FROM amount_units WHERE name = 'piece'")).fetchone()
        return row[0] if row else None

    # Ingredient lookup or create
    ing_cache: dict[str, int] = {}

    def get_or_create_ingredient(name: str) -> int:
        key = name.lower()
        if key in ing_cache:
            return ing_cache[key]
        row = conn.execute(
            text("SELECT id FROM ingredients WHERE LOWER(name) = :n"), {"n": key}
        ).fetchone()
        if row:
            ing_cache[key] = row[0]
            return row[0]
        # Check French translations
        row = conn.execute(
            text(
                "SELECT ingredient_id FROM ingredient_translations"
                " WHERE LOWER(name) = :n AND lang = 'fr'"
            ),
            {"n": key},
        ).fetchone()
        if row:
            ing_cache[key] = row[0]
            return row[0]
        # Create new ingredient (type = "Other")
        other_type = conn.execute(
            text("SELECT id FROM ingredient_types WHERE name = 'Other'")
        ).fetchone()
        type_id = other_type[0] if other_type else None
        new_id = conn.execute(
            text("INSERT INTO ingredients (name, type_id) VALUES (:n, :t) RETURNING id"),
            {"n": name, "t": type_id},
        ).fetchone()[0]
        # Store French translation so the name is searchable in FR UI
        conn.execute(
            text(
                "INSERT INTO ingredient_translations (ingredient_id, lang, name)"
                " VALUES (:id, 'fr', :n) ON CONFLICT DO NOTHING"
            ),
            {"id": new_id, "n": name},
        )
        ing_cache[key] = new_id
        return new_id

    # Preload caches for types and units
    type_cache: dict[str, int] = {}
    unit_cache: dict[str, int] = {}

    recipes_data = json.loads((DATA_DIR / "recipes.json").read_text(encoding="utf-8"))

    rng = random.Random(42)
    inserted = 0

    for entry in recipes_data:
        user_id = rng.choice(user_ids)

        # Resolve type
        type_name = entry.get("type_name", "Main course")
        if type_name not in type_cache:
            type_cache[type_name] = get_type_id(type_name)
        type_id = type_cache[type_name]

        # Copy images to UPLOADS_DIR
        image_filename = entry.get("image_filename")
        if image_filename:
            for prefix in ["", "thumb_"]:
                src = IMAGES_SRC / f"{prefix}{image_filename}"
                dst = UPLOADS_DIR / f"{prefix}{image_filename}"
                if src.exists() and not dst.exists():
                    try:
                        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                    except OSError as exc:
                        print(f"  [warn] could not copy {src.name}: {exc}")
                        image_filename = None
                        break

        # Insert recipe
        recipe_id = conn.execute(
            text(
                "INSERT INTO recipes"
                " (user_id, title, description, type_id, servings, image_filename)"
                " VALUES (:u, :t, :d, :ty, :s, :img) RETURNING id"
            ),
            {
                "u": user_id,
                "t": entry["title"],
                "d": entry.get("description"),
                "ty": type_id,
                "s": entry.get("servings"),
                "img": image_filename,
            },
        ).fetchone()[0]

        # Insert ingredients (all ungrouped)
        for ing in entry.get("ingredients", []):
            unit_name = ing.get("unit_name", "piece")
            if unit_name not in unit_cache:
                unit_cache[unit_name] = get_unit_id(unit_name)
            unit_id = unit_cache[unit_name]
            if unit_id is None:
                continue
            try:
                ing_id = get_or_create_ingredient(ing["name"])
                conn.execute(
                    text(
                        "INSERT INTO recipe_ingredients"
                        " (recipe_id, ingredient_id, amount, unit_id)"
                        " VALUES (:r, :i, :a, :u)"
                    ),
                    {"r": recipe_id, "i": ing_id, "a": ing["amount"], "u": unit_id},
                )
            except Exception as exc:
                print(f"  [ing warn] {ing['name']!r}: {exc}")

        # Insert steps
        for pos, step in enumerate(entry.get("steps", []), start=1):
            conn.execute(
                text(
                    "INSERT INTO steps (recipe_id, position, description, duration)"
                    " VALUES (:r, :p, :d, :dur)"
                ),
                {
                    "r": recipe_id,
                    "p": pos,
                    "d": step["description"],
                    "dur": step.get("duration"),
                },
            )

        inserted += 1
        print(f"  [{inserted}/50] {entry['title']}")

    print(f"[seed_demo] Inserted {inserted} recipes.")


def run() -> None:
    engine = create_engine(settings.database_url)
    with engine.begin() as conn:
        run_with_conn(conn)
    engine.dispose()


if __name__ == "__main__":
    run()
