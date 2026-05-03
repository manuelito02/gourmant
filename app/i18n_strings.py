# Strings catalog: marks runtime strings (from DB seed data, error messages, etc.)
# for Babel extraction. This file is never imported — it exists only so that
# pybabel extract picks up strings that can't be found via template or gettext_for.


def _(s):
    return s


# ── Amount unit names (from seed migration) ───────────────────────────────────
_("gram")
_("kilogram")
_("milliliter")
_("liter")
_("centiliter")
_("deciliter")
_("teaspoon")
_("tablespoon")
_("cup")
_("piece")
_("pinch")
_("to taste")

# ── Ingredient types (from seed migration) ────────────────────────────────────
_("Vegetable")
_("Fruit")
_("Meat")
_("Fish")
_("Seafood")
_("Dairy")
_("Egg")
_("Grain")
_("Legume")
_("Nut")
_("Spice")
_("Herb")
_("Oil")
_("Sweetener")
_("Condiment")
_("Beverage")
_("Other")

# ── Recipe types (from seed migration) ────────────────────────────────────────
_("Starter")
_("Main course")
_("Dessert")
_("Sauce")
_("Side dish")
_("Soup")
_("Salad")
_("Breakfast")
_("Snack")
_("Beverage")

# ── Error / feedback messages used in Python (not in templates) ───────────────
_("Password is too weak.")
_("Invalid email or password")
_("Not authenticated")
_("Recipe not found")
_("Not your recipe")
_("Name is required")
_("Ingredient already exists")
_("My Recipes")
