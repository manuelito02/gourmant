"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-11 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# ── Reference data ────────────────────────────────────────────────────────────

INGREDIENT_TYPES = [
    "Vegetable", "Fruit", "Meat", "Fish", "Seafood", "Dairy", "Egg",
    "Grain", "Legume", "Nut", "Spice", "Herb", "Oil", "Sweetener",
    "Condiment", "Beverage", "Other",
]

AMOUNT_UNITS = [
    ("gram", "g"),
    ("kilogram", "kg"),
    ("milliliter", "ml"),
    ("liter", "L"),
    ("centiliter", "cl"),
    ("deciliter", "dl"),
    ("teaspoon", "tsp"),
    ("tablespoon", "tbsp"),
    ("cup", "cup"),
    ("piece", "pc"),
    ("pinch", "pinch"),
    ("to taste", "to taste"),
]

RECIPE_TYPES = [
    "Starter", "Main course", "Dessert", "Sauce", "Side dish",
    "Soup", "Salad", "Breakfast", "Snack", "Beverage",
]

# name → ingredient type name
INGREDIENTS: list[tuple[str, str]] = [
    # Vegetables
    ("onion", "Vegetable"), ("garlic", "Vegetable"), ("tomato", "Vegetable"),
    ("carrot", "Vegetable"), ("potato", "Vegetable"), ("sweet potato", "Vegetable"),
    ("bell pepper", "Vegetable"), ("zucchini", "Vegetable"), ("eggplant", "Vegetable"),
    ("broccoli", "Vegetable"), ("cauliflower", "Vegetable"), ("spinach", "Vegetable"),
    ("kale", "Vegetable"), ("lettuce", "Vegetable"), ("cucumber", "Vegetable"),
    ("celery", "Vegetable"), ("leek", "Vegetable"), ("mushroom", "Vegetable"),
    ("peas", "Vegetable"), ("corn", "Vegetable"), ("green beans", "Vegetable"),
    ("asparagus", "Vegetable"), ("pumpkin", "Vegetable"), ("cabbage", "Vegetable"),
    ("beetroot", "Vegetable"), ("radish", "Vegetable"),
    # Fruits
    ("lemon", "Fruit"), ("lime", "Fruit"), ("orange", "Fruit"), ("apple", "Fruit"),
    ("banana", "Fruit"), ("avocado", "Fruit"), ("strawberry", "Fruit"),
    ("blueberry", "Fruit"), ("raspberry", "Fruit"), ("mango", "Fruit"),
    ("pineapple", "Fruit"), ("peach", "Fruit"), ("pear", "Fruit"),
    ("cherry", "Fruit"), ("grape", "Fruit"), ("coconut", "Fruit"),
    # Meat
    ("chicken breast", "Meat"), ("chicken thigh", "Meat"), ("ground beef", "Meat"),
    ("beef steak", "Meat"), ("pork chop", "Meat"), ("bacon", "Meat"),
    ("lamb shoulder", "Meat"), ("sausage", "Meat"), ("ham", "Meat"),
    ("turkey breast", "Meat"), ("duck breast", "Meat"), ("veal", "Meat"),
    # Fish
    ("salmon", "Fish"), ("tuna", "Fish"), ("cod", "Fish"), ("sea bass", "Fish"),
    ("trout", "Fish"), ("sardines", "Fish"), ("anchovies", "Fish"), ("mackerel", "Fish"),
    # Seafood
    ("shrimp", "Seafood"), ("mussels", "Seafood"), ("squid", "Seafood"),
    ("scallops", "Seafood"), ("crab", "Seafood"), ("clams", "Seafood"),
    ("octopus", "Seafood"),
    # Dairy
    ("butter", "Dairy"), ("milk", "Dairy"), ("cream", "Dairy"), ("heavy cream", "Dairy"),
    ("parmesan", "Dairy"), ("mozzarella", "Dairy"), ("cheddar", "Dairy"),
    ("feta", "Dairy"), ("gruyère", "Dairy"), ("brie", "Dairy"), ("yogurt", "Dairy"),
    ("sour cream", "Dairy"), ("cream cheese", "Dairy"), ("ricotta", "Dairy"),
    ("gouda", "Dairy"),
    # Egg
    ("egg", "Egg"),
    # Grains
    ("all-purpose flour", "Grain"), ("bread flour", "Grain"), ("rice", "Grain"),
    ("spaghetti", "Grain"), ("penne", "Grain"), ("tagliatelle", "Grain"),
    ("lasagna sheets", "Grain"), ("breadcrumbs", "Grain"), ("oats", "Grain"),
    ("couscous", "Grain"), ("quinoa", "Grain"), ("polenta", "Grain"),
    ("cornstarch", "Grain"), ("semolina", "Grain"),
    # Legumes
    ("chickpeas", "Legume"), ("lentils", "Legume"), ("black beans", "Legume"),
    ("kidney beans", "Legume"), ("white beans", "Legume"), ("tofu", "Legume"),
    ("edamame", "Legume"),
    # Nuts
    ("almonds", "Nut"), ("walnuts", "Nut"), ("cashews", "Nut"), ("pine nuts", "Nut"),
    ("hazelnuts", "Nut"), ("pecans", "Nut"), ("pistachios", "Nut"), ("peanuts", "Nut"),
    ("sesame seeds", "Nut"),
    # Spices
    ("salt", "Spice"), ("black pepper", "Spice"), ("paprika", "Spice"),
    ("smoked paprika", "Spice"), ("cumin", "Spice"), ("coriander", "Spice"),
    ("turmeric", "Spice"), ("cinnamon", "Spice"), ("chili flakes", "Spice"),
    ("cayenne pepper", "Spice"), ("ground ginger", "Spice"), ("garlic powder", "Spice"),
    ("onion powder", "Spice"), ("nutmeg", "Spice"), ("cloves", "Spice"),
    ("cardamom", "Spice"), ("star anise", "Spice"), ("saffron", "Spice"),
    ("vanilla extract", "Spice"),
    # Herbs
    ("basil", "Herb"), ("oregano", "Herb"), ("thyme", "Herb"), ("rosemary", "Herb"),
    ("parsley", "Herb"), ("cilantro", "Herb"), ("mint", "Herb"), ("dill", "Herb"),
    ("bay leaf", "Herb"), ("sage", "Herb"), ("tarragon", "Herb"), ("chives", "Herb"),
    ("lemongrass", "Herb"),
    # Oils
    ("olive oil", "Oil"), ("extra virgin olive oil", "Oil"), ("vegetable oil", "Oil"),
    ("sunflower oil", "Oil"), ("sesame oil", "Oil"), ("coconut oil", "Oil"),
    # Sweeteners
    ("sugar", "Sweetener"), ("brown sugar", "Sweetener"), ("powdered sugar", "Sweetener"),
    ("honey", "Sweetener"), ("maple syrup", "Sweetener"),
    # Condiments
    ("tomato paste", "Condiment"), ("tomato sauce", "Condiment"), ("soy sauce", "Condiment"),
    ("white vinegar", "Condiment"), ("balsamic vinegar", "Condiment"),
    ("dijon mustard", "Condiment"), ("ketchup", "Condiment"), ("hot sauce", "Condiment"),
    ("worcestershire sauce", "Condiment"), ("fish sauce", "Condiment"),
    ("coconut milk", "Condiment"), ("chicken stock", "Condiment"),
    ("beef stock", "Condiment"), ("vegetable stock", "Condiment"),
    ("mayonnaise", "Condiment"), ("tahini", "Condiment"), ("miso paste", "Condiment"),
    ("oyster sauce", "Condiment"), ("hoisin sauce", "Condiment"),
    # Beverages
    ("white wine", "Beverage"), ("red wine", "Beverage"), ("beer", "Beverage"),
    # Other
    ("baking powder", "Other"), ("baking soda", "Other"), ("dry yeast", "Other"),
    ("dark chocolate", "Other"), ("cocoa powder", "Other"), ("gelatin", "Other"),
]


def upgrade() -> None:
    # ── Users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

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
        sa.UniqueConstraint("abbreviation"),
        sa.UniqueConstraint("name"),
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

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, name FROM ingredient_types")).fetchall()
    type_id_by_name = {row[1]: row[0] for row in rows}
    ingredients_table = sa.table(
        "ingredients",
        sa.column("name", sa.String),
        sa.column("type_id", sa.Integer),
    )
    op.bulk_insert(
        ingredients_table,
        [
            {"name": name, "type_id": type_id_by_name[type_name]}
            for name, type_name in INGREDIENTS
            if type_name in type_id_by_name
        ],
    )

    # ── Recipes ───────────────────────────────────────────────────────────────
    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type_id", sa.Integer(), nullable=False),
        sa.Column("servings", sa.Integer(), nullable=True),
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

    # ── Ingredient groups ─────────────────────────────────────────────────────
    op.create_table(
        "recipe_ingredient_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── Recipe ↔ Ingredient join ──────────────────────────────────────────────
    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["recipe_ingredient_groups.id"]),
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
    op.drop_table("recipe_ingredient_groups")
    op.drop_index(op.f("ix_recipes_user_id"), table_name="recipes")
    op.drop_table("recipes")
    op.drop_index(op.f("ix_ingredients_name"), table_name="ingredients")
    op.drop_table("ingredients")
    op.drop_table("recipe_types")
    op.drop_table("amount_units")
    op.drop_table("ingredient_types")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
