"""add servings and seed ingredients

Revision ID: b3c9d2e1f4a0
Revises: a5f1816c5ed5
Create Date: 2026-04-11 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b3c9d2e1f4a0"
down_revision: str | Sequence[str] | None = "a5f1816c5ed5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# name → type name (must match INGREDIENT_TYPES in prior migration)
INGREDIENTS: list[tuple[str, str]] = [
    # Vegetables
    ("onion", "Vegetable"),
    ("garlic", "Vegetable"),
    ("tomato", "Vegetable"),
    ("carrot", "Vegetable"),
    ("potato", "Vegetable"),
    ("sweet potato", "Vegetable"),
    ("bell pepper", "Vegetable"),
    ("zucchini", "Vegetable"),
    ("eggplant", "Vegetable"),
    ("broccoli", "Vegetable"),
    ("cauliflower", "Vegetable"),
    ("spinach", "Vegetable"),
    ("kale", "Vegetable"),
    ("lettuce", "Vegetable"),
    ("cucumber", "Vegetable"),
    ("celery", "Vegetable"),
    ("leek", "Vegetable"),
    ("mushroom", "Vegetable"),
    ("peas", "Vegetable"),
    ("corn", "Vegetable"),
    ("green beans", "Vegetable"),
    ("asparagus", "Vegetable"),
    ("pumpkin", "Vegetable"),
    ("cabbage", "Vegetable"),
    ("beetroot", "Vegetable"),
    ("radish", "Vegetable"),
    # Fruits
    ("lemon", "Fruit"),
    ("lime", "Fruit"),
    ("orange", "Fruit"),
    ("apple", "Fruit"),
    ("banana", "Fruit"),
    ("avocado", "Fruit"),
    ("strawberry", "Fruit"),
    ("blueberry", "Fruit"),
    ("raspberry", "Fruit"),
    ("mango", "Fruit"),
    ("pineapple", "Fruit"),
    ("peach", "Fruit"),
    ("pear", "Fruit"),
    ("cherry", "Fruit"),
    ("grape", "Fruit"),
    ("coconut", "Fruit"),
    # Meat
    ("chicken breast", "Meat"),
    ("chicken thigh", "Meat"),
    ("ground beef", "Meat"),
    ("beef steak", "Meat"),
    ("pork chop", "Meat"),
    ("bacon", "Meat"),
    ("lamb shoulder", "Meat"),
    ("sausage", "Meat"),
    ("ham", "Meat"),
    ("turkey breast", "Meat"),
    ("duck breast", "Meat"),
    ("veal", "Meat"),
    # Fish
    ("salmon", "Fish"),
    ("tuna", "Fish"),
    ("cod", "Fish"),
    ("sea bass", "Fish"),
    ("trout", "Fish"),
    ("sardines", "Fish"),
    ("anchovies", "Fish"),
    ("mackerel", "Fish"),
    # Seafood
    ("shrimp", "Seafood"),
    ("mussels", "Seafood"),
    ("squid", "Seafood"),
    ("scallops", "Seafood"),
    ("crab", "Seafood"),
    ("clams", "Seafood"),
    ("octopus", "Seafood"),
    # Dairy
    ("butter", "Dairy"),
    ("milk", "Dairy"),
    ("cream", "Dairy"),
    ("heavy cream", "Dairy"),
    ("parmesan", "Dairy"),
    ("mozzarella", "Dairy"),
    ("cheddar", "Dairy"),
    ("feta", "Dairy"),
    ("gruyère", "Dairy"),
    ("brie", "Dairy"),
    ("yogurt", "Dairy"),
    ("sour cream", "Dairy"),
    ("cream cheese", "Dairy"),
    ("ricotta", "Dairy"),
    ("gouda", "Dairy"),
    # Egg
    ("egg", "Egg"),
    # Grains
    ("all-purpose flour", "Grain"),
    ("bread flour", "Grain"),
    ("rice", "Grain"),
    ("spaghetti", "Grain"),
    ("penne", "Grain"),
    ("tagliatelle", "Grain"),
    ("lasagna sheets", "Grain"),
    ("breadcrumbs", "Grain"),
    ("oats", "Grain"),
    ("couscous", "Grain"),
    ("quinoa", "Grain"),
    ("polenta", "Grain"),
    ("cornstarch", "Grain"),
    ("semolina", "Grain"),
    # Legumes
    ("chickpeas", "Legume"),
    ("lentils", "Legume"),
    ("black beans", "Legume"),
    ("kidney beans", "Legume"),
    ("white beans", "Legume"),
    ("tofu", "Legume"),
    ("edamame", "Legume"),
    # Nuts
    ("almonds", "Nut"),
    ("walnuts", "Nut"),
    ("cashews", "Nut"),
    ("pine nuts", "Nut"),
    ("hazelnuts", "Nut"),
    ("pecans", "Nut"),
    ("pistachios", "Nut"),
    ("peanuts", "Nut"),
    ("sesame seeds", "Nut"),
    # Spices
    ("salt", "Spice"),
    ("black pepper", "Spice"),
    ("paprika", "Spice"),
    ("smoked paprika", "Spice"),
    ("cumin", "Spice"),
    ("coriander", "Spice"),
    ("turmeric", "Spice"),
    ("cinnamon", "Spice"),
    ("chili flakes", "Spice"),
    ("cayenne pepper", "Spice"),
    ("ground ginger", "Spice"),
    ("garlic powder", "Spice"),
    ("onion powder", "Spice"),
    ("nutmeg", "Spice"),
    ("cloves", "Spice"),
    ("cardamom", "Spice"),
    ("star anise", "Spice"),
    ("saffron", "Spice"),
    ("vanilla extract", "Spice"),
    # Herbs
    ("basil", "Herb"),
    ("oregano", "Herb"),
    ("thyme", "Herb"),
    ("rosemary", "Herb"),
    ("parsley", "Herb"),
    ("cilantro", "Herb"),
    ("mint", "Herb"),
    ("dill", "Herb"),
    ("bay leaf", "Herb"),
    ("sage", "Herb"),
    ("tarragon", "Herb"),
    ("chives", "Herb"),
    ("lemongrass", "Herb"),
    # Oils
    ("olive oil", "Oil"),
    ("extra virgin olive oil", "Oil"),
    ("vegetable oil", "Oil"),
    ("sunflower oil", "Oil"),
    ("sesame oil", "Oil"),
    ("coconut oil", "Oil"),
    # Sweeteners
    ("sugar", "Sweetener"),
    ("brown sugar", "Sweetener"),
    ("powdered sugar", "Sweetener"),
    ("honey", "Sweetener"),
    ("maple syrup", "Sweetener"),
    # Condiments
    ("tomato paste", "Condiment"),
    ("tomato sauce", "Condiment"),
    ("soy sauce", "Condiment"),
    ("white vinegar", "Condiment"),
    ("balsamic vinegar", "Condiment"),
    ("dijon mustard", "Condiment"),
    ("ketchup", "Condiment"),
    ("hot sauce", "Condiment"),
    ("worcestershire sauce", "Condiment"),
    ("fish sauce", "Condiment"),
    ("coconut milk", "Condiment"),
    ("chicken stock", "Condiment"),
    ("beef stock", "Condiment"),
    ("vegetable stock", "Condiment"),
    ("mayonnaise", "Condiment"),
    ("tahini", "Condiment"),
    ("miso paste", "Condiment"),
    ("oyster sauce", "Condiment"),
    ("hoisin sauce", "Condiment"),
    # Beverages
    ("white wine", "Beverage"),
    ("red wine", "Beverage"),
    ("beer", "Beverage"),
    # Other
    ("baking powder", "Other"),
    ("baking soda", "Other"),
    ("dry yeast", "Other"),
    ("dark chocolate", "Other"),
    ("cocoa powder", "Other"),
    ("gelatin", "Other"),
]


def upgrade() -> None:
    op.add_column("recipes", sa.Column("servings", sa.Integer(), nullable=True))

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


def downgrade() -> None:
    conn = op.get_bind()
    names = [name for name, _ in INGREDIENTS]
    conn.execute(
        sa.text("DELETE FROM ingredients WHERE name = ANY(:names)"),
        {"names": names},
    )
    op.drop_column("recipes", "servings")
