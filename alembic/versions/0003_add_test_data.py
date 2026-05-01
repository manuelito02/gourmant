"""Add demo users (Bob and Charly) with sample recipes

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-12 00:00:00.000000

"""

from collections.abc import Sequence

import bcrypt
from sqlalchemy import text

from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _get(conn, table: str, col: str, val: str) -> int:
    row = conn.execute(
        text(f"SELECT id FROM {table} WHERE {col} = :v"),
        {"v": val},
    ).fetchone()
    if row is None:
        raise ValueError(f"{table}.{col}={val!r} not found")
    return row[0]


def _insert_recipe(conn, user_id, title, description, type_id, servings) -> int:
    row = conn.execute(
        text(
            "INSERT INTO recipes (user_id, title, description, type_id, servings)"
            " VALUES (:u, :t, :d, :ty, :s) RETURNING id"
        ),
        {"u": user_id, "t": title, "d": description, "ty": type_id, "s": servings},
    ).fetchone()
    return row[0]


def _insert_group(conn, recipe_id, name, position) -> int:
    row = conn.execute(
        text(
            "INSERT INTO recipe_ingredient_groups (recipe_id, name, position)"
            " VALUES (:r, :n, :p) RETURNING id"
        ),
        {"r": recipe_id, "n": name, "p": position},
    ).fetchone()
    return row[0]


def _insert_ingredient(conn, recipe_id, ing_id, amount, unit_id, group_id=None):
    conn.execute(
        text(
            "INSERT INTO recipe_ingredients (recipe_id, ingredient_id, amount, unit_id, group_id)"
            " VALUES (:r, :i, :a, :u, :g)"
        ),
        {"r": recipe_id, "i": ing_id, "a": amount, "u": unit_id, "g": group_id},
    )


def _insert_step(conn, recipe_id, position, description, duration=None):
    conn.execute(
        text(
            "INSERT INTO steps (recipe_id, position, description, duration)"
            " VALUES (:r, :p, :d, :du)"
        ),
        {"r": recipe_id, "p": position, "d": description, "du": duration},
    )


def upgrade() -> None:
    conn = op.get_bind()

    # ── Users ──────────────────────────────────────────────────────────────────
    bob_hash = bcrypt.hashpw(b"bob-rocks-42", bcrypt.gensalt()).decode()
    charly_hash = bcrypt.hashpw(b"charly-cooks-42", bcrypt.gensalt()).decode()

    bob_id = conn.execute(
        text(
            "INSERT INTO users (first_name, last_name, email, hashed_password)"
            " VALUES ('Bob', 'Martin', 'bob@example.com', :h) RETURNING id"
        ),
        {"h": bob_hash},
    ).fetchone()[0]

    charly_id = conn.execute(
        text(
            "INSERT INTO users (first_name, last_name, email, hashed_password)"
            " VALUES ('Charly', 'Dupont', 'charly@example.com', :h) RETURNING id"
        ),
        {"h": charly_hash},
    ).fetchone()[0]

    # ── Lookup helpers ─────────────────────────────────────────────────────────
    def ing(name: str) -> int:
        return _get(conn, "ingredients", "name", name)

    def unit(abbr: str) -> int:
        return _get(conn, "amount_units", "abbreviation", abbr)

    def rtype(name: str) -> int:
        return _get(conn, "recipe_types", "name", name)

    # Units
    g = unit("g")
    ml = unit("ml")
    liter = unit("L")
    tsp = unit("tsp")
    tbsp = unit("tbsp")
    pc = unit("pc")
    to_taste = unit("to taste")

    # Recipe types
    main = rtype("Main course")
    salad = rtype("Salad")
    dessert = rtype("Dessert")
    soup = rtype("Soup")

    # ── Bob's recipes ──────────────────────────────────────────────────────────

    # 1. Spaghetti Bolognese
    r1 = _insert_recipe(
        conn,
        bob_id,
        "Spaghetti Bolognese",
        "A hearty Italian pasta dish with a rich tomato and meat sauce.",
        main,
        4,
    )
    for ing_name, amount, unit_id in [
        ("spaghetti", 400, g),
        ("ground beef", 300, g),
        ("tomato", 3, pc),
        ("onion", 1, pc),
        ("garlic", 3, pc),
        ("olive oil", 2, tbsp),
        ("tomato paste", 1, tbsp),
        ("salt", 1, to_taste),
        ("black pepper", 1, to_taste),
    ]:
        _insert_ingredient(conn, r1, ing(ing_name), amount, unit_id)
    for pos, desc, dur in [
        (1, "Boil a large pot of salted water and cook the spaghetti until al dente.", 10),
        (2, "Dice the onion and garlic. Heat olive oil in a pan and sauté until softened.", 5),
        (3, "Add ground beef and cook until browned. Stir in tomato paste.", 8),
        (4, "Add chopped tomatoes and simmer the sauce over low heat until thick.", 25),
        (5, "Drain the pasta, toss with the sauce, and serve immediately.", 2),
    ]:
        _insert_step(conn, r1, pos, desc, dur)

    # 2. Caesar Salad
    r2 = _insert_recipe(
        conn,
        bob_id,
        "Caesar Salad",
        "A classic salad with a tangy lemony dressing and parmesan.",
        salad,
        2,
    )
    for ing_name, amount, unit_id in [
        ("lettuce", 1, pc),
        ("parmesan", 50, g),
        ("lemon", 1, pc),
        ("olive oil", 3, tbsp),
        ("garlic", 1, pc),
        ("salt", 1, to_taste),
        ("black pepper", 1, to_taste),
    ]:
        _insert_ingredient(conn, r2, ing(ing_name), amount, unit_id)
    for pos, desc, dur in [
        (1, "Wash and tear the lettuce into bite-sized pieces.", 3),
        (2, "Whisk together olive oil, lemon juice, minced garlic, salt, and pepper.", 3),
        (3, "Toss the lettuce with the dressing and top with grated parmesan.", 2),
    ]:
        _insert_step(conn, r2, pos, desc, dur)

    # 3. Chocolate Mousse
    r3 = _insert_recipe(
        conn,
        bob_id,
        "Chocolate Mousse",
        "Light and airy mousse — perfect for dinner parties.",
        dessert,
        6,
    )
    for ing_name, amount, unit_id in [
        ("egg", 3, pc),
        ("sugar", 80, g),
        ("heavy cream", 300, ml),
        ("vanilla extract", 1, tsp),
    ]:
        _insert_ingredient(conn, r3, ing(ing_name), amount, unit_id)
    for pos, desc, dur in [
        (1, "Separate the eggs. Beat the yolks with sugar until pale and fluffy.", 5),
        (2, "Whip the heavy cream with vanilla extract until soft peaks form.", 5),
        (3, "Whisk the egg whites until stiff peaks form.", 5),
        (4, "Gently fold the cream and egg whites into the yolk mixture.", 3),
        (5, "Pour into glasses and refrigerate for at least 2 hours.", 120),
    ]:
        _insert_step(conn, r3, pos, desc, dur)

    # ── Charly's recipes ───────────────────────────────────────────────────────

    # 4. French Onion Soup
    r4 = _insert_recipe(
        conn,
        charly_id,
        "French Onion Soup",
        "Deeply caramelized onions in a rich beef broth — a French bistro staple.",
        soup,
        4,
    )
    for ing_name, amount, unit_id in [
        ("onion", 6, pc),
        ("butter", 50, g),
        ("beef stock", 1, liter),
        ("thyme", 2, tsp),
        ("salt", 1, to_taste),
        ("black pepper", 1, to_taste),
    ]:
        _insert_ingredient(conn, r4, ing(ing_name), amount, unit_id)
    for pos, desc, dur in [
        (1, "Slice the onions thinly. Melt butter in a heavy pot over medium heat.", 5),
        (2, "Cook the onions slowly, stirring occasionally, until deeply caramelized.", 45),
        (3, "Add beef stock and thyme. Simmer for 15 minutes. Season to taste.", 15),
        (4, "Ladle into oven-safe bowls, top with bread and gruyère, and gratinate.", 5),
    ]:
        _insert_step(conn, r4, pos, desc, dur)

    # 5. Quiche Lorraine
    r5 = _insert_recipe(
        conn,
        charly_id,
        "Quiche Lorraine",
        "A classic French tart with bacon and gruyère in a creamy egg custard.",
        main,
        6,
    )
    g5_pastry = _insert_group(conn, r5, "Pastry", 0)
    for ing_name, amount, unit_id in [
        ("all-purpose flour", 200, g),
        ("butter", 100, g),
        ("salt", 1, to_taste),
    ]:
        _insert_ingredient(conn, r5, ing(ing_name), amount, unit_id, g5_pastry)
    g5_filling = _insert_group(conn, r5, "Filling", 1)
    for ing_name, amount, unit_id in [
        ("egg", 3, pc),
        ("cream", 200, ml),
        ("bacon", 150, g),
        ("gruyère", 100, g),
        ("salt", 1, to_taste),
        ("black pepper", 1, to_taste),
    ]:
        _insert_ingredient(conn, r5, ing(ing_name), amount, unit_id, g5_filling)
    for pos, desc, dur in [
        (
            1,
            "Mix flour, cold diced butter, and a pinch of salt until crumbly."
            " Add cold water and form a dough. Chill 30 min.",
            35,
        ),
        (2, "Preheat oven to 180 °C. Roll out the dough and press into a tart pan.", 10),
        (3, "Dice bacon and fry until crispy. Scatter over the pastry base.", 8),
        (
            4,
            "Whisk eggs with cream, season generously."
            " Pour over the bacon. Top with grated gruyère.",
            5,
        ),
        (5, "Bake until golden and set, about 35 minutes.", 35),
    ]:
        _insert_step(conn, r5, pos, desc, dur)

    # 6. Tarte Tatin
    r6 = _insert_recipe(
        conn,
        charly_id,
        "Tarte Tatin",
        "Upside-down caramelized apple tart — a French classic.",
        dessert,
        8,
    )
    g6_apples = _insert_group(conn, r6, "Caramel apples", 0)
    for ing_name, amount, unit_id in [
        ("apple", 6, pc),
        ("sugar", 150, g),
        ("butter", 80, g),
    ]:
        _insert_ingredient(conn, r6, ing(ing_name), amount, unit_id, g6_apples)
    g6_pastry = _insert_group(conn, r6, "Pastry", 1)
    for ing_name, amount, unit_id in [
        ("all-purpose flour", 200, g),
        ("butter", 80, g),
        ("sugar", 1, tbsp),
        ("salt", 1, to_taste),
    ]:
        _insert_ingredient(conn, r6, ing(ing_name), amount, unit_id, g6_pastry)
    for pos, desc, dur in [
        (1, "Peel, core, and quarter the apples.", 10),
        (2, "Melt sugar in an oven-safe pan until golden caramel forms. Add butter and stir.", 10),
        (3, "Arrange apple quarters tightly over the caramel. Cook on medium heat.", 10),
        (4, "Roll out the pastry and drape over the apples, tucking in the edges.", 5),
        (5, "Bake at 200 °C until the pastry is golden and crisp.", 25),
        (6, "Let cool for 5 minutes, then invert carefully onto a serving plate.", 5),
    ]:
        _insert_step(conn, r6, pos, desc, dur)


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DELETE FROM users WHERE email IN ('bob@example.com', 'charly@example.com')"))
