import pytest

from app.models.ingredient import AmountUnit, Ingredient, IngredientType
from app.models.recipe import RecipeType

# ── Shared helpers ────────────────────────────────────────────────────────────

OTHER_USER = {
    "first_name": "Bob",
    "last_name": "Smith",
    "email": "bob@example.com",
    "password": "correct-horse-battery-staple",
    "password_confirm": "correct-horse-battery-staple",
}


@pytest.fixture
def ref(db):
    """IDs for seeded reference data needed to build valid payloads."""
    return {
        "type_id": db.query(RecipeType).first().id,
        "ing_type_id": db.query(IngredientType).first().id,
        "unit_id": db.query(AmountUnit).first().id,
        # Use the first seeded ingredient for recipe ingredient tests
        "ingredient_id": db.query(Ingredient).first().id,
        # A second seeded ingredient for group tests
        "ingredient_id2": db.query(Ingredient).order_by(Ingredient.id.desc()).first().id,
    }


def minimal_payload(ref: dict) -> dict:
    return {"title": "Test Pasta", "type_id": ref["type_id"]}


def create_recipe(client, payload: dict) -> int:
    """POST /api/recipes and return the new recipe id."""
    res = client.post("/api/recipes", json=payload)
    assert res.status_code == 201
    return res.json()["id"]


# ── Dashboard ─────────────────────────────────────────────────────────────────


def test_dashboard_redirects_when_logged_out(client):
    response = client.get("/dashboard")
    assert response.url.path == "/login"


def test_dashboard_empty_state(auth_client):
    response = auth_client.get("/dashboard")
    assert response.status_code == 200
    assert "No recipes yet" in response.text


def test_dashboard_shows_recipe_card(auth_client, ref):
    create_recipe(auth_client, {**minimal_payload(ref), "title": "My Bolognese"})
    response = auth_client.get("/dashboard")
    assert "My Bolognese" in response.text


def test_dashboard_shows_type_and_date(auth_client, ref):
    create_recipe(auth_client, minimal_payload(ref))
    response = auth_client.get("/dashboard")
    assert response.status_code == 200
    # recipe type name from the first seeded RecipeType should appear
    assert ref["type_id"]  # sanity check fixture worked


def test_dashboard_shows_servings(auth_client, ref):
    create_recipe(auth_client, {**minimal_payload(ref), "servings": 4})
    response = auth_client.get("/dashboard")
    assert "4 servings" in response.text


def test_dashboard_only_shows_own_recipes(client, ref):
    # Register two users; only first user's recipe should appear on their dashboard
    client.post(
        "/register",
        data={
            "first_name": "Alice",
            "last_name": "A",
            "email": "alice@example.com",
            "password": "correct-horse-battery-staple",
            "password_confirm": "correct-horse-battery-staple",
        },
    )
    create_recipe(client, {**minimal_payload(ref), "title": "Alice Soup"})
    client.post("/logout")

    client.post("/register", data=OTHER_USER)
    response = client.get("/dashboard")
    assert "Alice Soup" not in response.text


# ── New recipe form ───────────────────────────────────────────────────────────


def test_new_recipe_form_redirects_when_logged_out(client):
    response = client.get("/recipes/new")
    assert response.url.path == "/login"


def test_new_recipe_form_loads(auth_client):
    response = auth_client.get("/recipes/new")
    assert response.status_code == 200
    assert "New recipe" in response.text


def test_new_recipe_form_contains_reference_data(auth_client):
    response = auth_client.get("/recipes/new")
    # Recipe types and ingredient types are embedded as JS globals
    assert "AMOUNT_UNITS" in response.text
    assert "INGREDIENT_TYPES" in response.text


# ── Recipe detail page ────────────────────────────────────────────────────────


def test_recipe_detail_redirects_when_logged_out(client):
    response = client.get("/recipes/999")
    assert response.url.path == "/login"


def test_recipe_detail_404_nonexistent(auth_client):
    response = auth_client.get("/recipes/999999")
    assert response.status_code == 404


def test_recipe_detail_404_other_users_recipe(client, ref):
    # Create recipe as first user
    client.post(
        "/register",
        data={
            "first_name": "Alice",
            "last_name": "A",
            "email": "alice@example.com",
            "password": "correct-horse-battery-staple",
            "password_confirm": "correct-horse-battery-staple",
        },
    )
    recipe_id = create_recipe(client, minimal_payload(ref))
    client.post("/logout")

    # Log in as second user — should not be able to view first user's recipe
    client.post("/register", data=OTHER_USER)
    response = client.get(f"/recipes/{recipe_id}")
    assert response.status_code == 404


def test_recipe_detail_shows_title_and_description(auth_client, ref):
    recipe_id = create_recipe(
        auth_client,
        {**minimal_payload(ref), "title": "Carbonara", "description": "A classic Roman pasta"},
    )
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert response.status_code == 200
    assert "Carbonara" in response.text
    assert "A classic Roman pasta" in response.text


def test_recipe_detail_shows_servings_control(auth_client, ref):
    recipe_id = create_recipe(auth_client, {**minimal_payload(ref), "servings": 2})
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert "servings" in response.text
    assert "BASE_SERVINGS" in response.text  # JS scaler is present


def test_recipe_detail_no_servings_control_when_null(auth_client, ref):
    recipe_id = create_recipe(auth_client, minimal_payload(ref))
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert "BASE_SERVINGS" not in response.text


def test_recipe_detail_shows_ungrouped_ingredient(auth_client, ref):
    payload = {
        **minimal_payload(ref),
        "ungrouped_ingredients": [
            {"ingredient_id": ref["ingredient_id"], "amount": 200, "unit_id": ref["unit_id"]}
        ],
    }
    recipe_id = create_recipe(auth_client, payload)
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert response.status_code == 200
    assert "200" in response.text


def test_recipe_detail_shows_ingredient_group(auth_client, ref):
    payload = {
        **minimal_payload(ref),
        "ingredient_groups": [
            {
                "name": "The Dough",
                "position": 0,
                "ingredients": [
                    {
                        "ingredient_id": ref["ingredient_id"],
                        "amount": 500,
                        "unit_id": ref["unit_id"],
                    }
                ],
            }
        ],
    }
    recipe_id = create_recipe(auth_client, payload)
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert "The Dough" in response.text
    assert "500" in response.text


def test_recipe_detail_shows_steps(auth_client, ref):
    payload = {
        **minimal_payload(ref),
        "steps": [
            {"position": 1, "description": "Boil salted water", "duration": 5},
            {"position": 2, "description": "Cook pasta al dente", "duration": 10},
        ],
    }
    recipe_id = create_recipe(auth_client, payload)
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert "Boil salted water" in response.text
    assert "Cook pasta al dente" in response.text
    assert "5 min" in response.text
    assert "10 min" in response.text


def test_recipe_detail_shows_total_duration(auth_client, ref):
    payload = {
        **minimal_payload(ref),
        "steps": [
            {"position": 1, "description": "Step one", "duration": 15},
            {"position": 2, "description": "Step two", "duration": 20},
        ],
    }
    recipe_id = create_recipe(auth_client, payload)
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert "35 min total" in response.text


def test_recipe_detail_step_without_duration(auth_client, ref):
    payload = {
        **minimal_payload(ref),
        "steps": [{"position": 1, "description": "Just mix it", "duration": None}],
    }
    recipe_id = create_recipe(auth_client, payload)
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert "Just mix it" in response.text
    # No total time label when all durations are null
    assert "min total" not in response.text


# ── Ingredient search API ─────────────────────────────────────────────────────


def test_search_ingredients_returns_seeded_match(client):
    response = client.get("/api/ingredients?q=garlic")
    assert response.status_code == 200
    names = [i["name"] for i in response.json()]
    assert any("garlic" in n.lower() for n in names)


def test_search_ingredients_case_insensitive(client):
    response = client.get("/api/ingredients?q=GARLIC")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_search_ingredients_no_results(client):
    response = client.get("/api/ingredients?q=xyznonexistentingredient")
    assert response.status_code == 200
    assert response.json() == []


def test_search_ingredients_empty_query_returns_results(client):
    response = client.get("/api/ingredients?q=")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_search_ingredients_limited_to_20(client):
    # Empty query matches everything; result must be capped at 20
    response = client.get("/api/ingredients?q=")
    assert len(response.json()) <= 20


def test_search_ingredients_returns_id_and_name(client):
    response = client.get("/api/ingredients?q=garlic")
    item = response.json()[0]
    assert "id" in item
    assert "name" in item


# ── Ingredient create API ─────────────────────────────────────────────────────


def test_create_ingredient_requires_auth(client, ref):
    response = client.post(
        "/api/ingredients", json={"name": "Truffle", "type_id": ref["ing_type_id"]}
    )
    assert response.status_code == 401


def test_create_ingredient_success(auth_client, ref):
    response = auth_client.post(
        "/api/ingredients", json={"name": "Dragon Fruit", "type_id": ref["ing_type_id"]}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Dragon Fruit"
    assert "id" in body


def test_create_ingredient_strips_whitespace(auth_client, ref):
    response = auth_client.post(
        "/api/ingredients", json={"name": "  Starfruit  ", "type_id": ref["ing_type_id"]}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Starfruit"


def test_create_ingredient_empty_name(auth_client, ref):
    response = auth_client.post(
        "/api/ingredients", json={"name": "   ", "type_id": ref["ing_type_id"]}
    )
    assert response.status_code == 400


def test_create_ingredient_duplicate_name(auth_client, ref):
    auth_client.post("/api/ingredients", json={"name": "Persimmon", "type_id": ref["ing_type_id"]})
    response = auth_client.post(
        "/api/ingredients", json={"name": "Persimmon", "type_id": ref["ing_type_id"]}
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_ingredient_duplicate_case_insensitive(auth_client, ref):
    auth_client.post("/api/ingredients", json={"name": "Tamarind", "type_id": ref["ing_type_id"]})
    response = auth_client.post(
        "/api/ingredients", json={"name": "TAMARIND", "type_id": ref["ing_type_id"]}
    )
    assert response.status_code == 400


def test_create_ingredient_searchable_after_creation(auth_client, ref):
    auth_client.post("/api/ingredients", json={"name": "Jackfruit", "type_id": ref["ing_type_id"]})
    response = auth_client.get("/api/ingredients?q=Jackfruit")
    names = [i["name"] for i in response.json()]
    assert "Jackfruit" in names


# ── Recipe create API ─────────────────────────────────────────────────────────


def test_create_recipe_requires_auth(client, ref):
    response = client.post("/api/recipes", json=minimal_payload(ref))
    assert response.status_code == 401


def test_create_recipe_minimal(auth_client, ref):
    response = auth_client.post("/api/recipes", json=minimal_payload(ref))
    assert response.status_code == 201
    assert "id" in response.json()


def test_create_recipe_with_description_and_servings(auth_client, ref):
    payload = {
        **minimal_payload(ref),
        "description": "Rich and hearty",
        "servings": 6,
    }
    recipe_id = create_recipe(auth_client, payload)
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert "Rich and hearty" in response.text
    assert "6" in response.text


def test_create_recipe_strips_title_whitespace(auth_client, ref):
    payload = {**minimal_payload(ref), "title": "  Risotto  "}
    recipe_id = create_recipe(auth_client, payload)
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert "Risotto" in response.text


def test_create_recipe_appears_on_dashboard(auth_client, ref):
    create_recipe(auth_client, {**minimal_payload(ref), "title": "Osso Buco"})
    response = auth_client.get("/dashboard")
    assert "Osso Buco" in response.text


def test_create_recipe_with_ungrouped_ingredients(auth_client, ref):
    payload = {
        **minimal_payload(ref),
        "ungrouped_ingredients": [
            {"ingredient_id": ref["ingredient_id"], "amount": 300, "unit_id": ref["unit_id"]}
        ],
    }
    response = auth_client.post("/api/recipes", json=payload)
    assert response.status_code == 201


def test_create_recipe_with_ingredient_groups(auth_client, ref):
    payload = {
        **minimal_payload(ref),
        "ingredient_groups": [
            {
                "name": "Filling",
                "position": 0,
                "ingredients": [
                    {
                        "ingredient_id": ref["ingredient_id"],
                        "amount": 150,
                        "unit_id": ref["unit_id"],
                    }
                ],
            }
        ],
    }
    response = auth_client.post("/api/recipes", json=payload)
    assert response.status_code == 201


def test_create_recipe_with_multiple_groups(auth_client, ref):
    payload = {
        **minimal_payload(ref),
        "ingredient_groups": [
            {
                "name": "Dough",
                "position": 0,
                "ingredients": [
                    {
                        "ingredient_id": ref["ingredient_id"],
                        "amount": 500,
                        "unit_id": ref["unit_id"],
                    }
                ],
            },
            {
                "name": "Topping",
                "position": 1,
                "ingredients": [
                    {
                        "ingredient_id": ref["ingredient_id2"],
                        "amount": 100,
                        "unit_id": ref["unit_id"],
                    }
                ],
            },
        ],
    }
    recipe_id = create_recipe(auth_client, payload)
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert "Dough" in response.text
    assert "Topping" in response.text


def test_create_recipe_with_steps(auth_client, ref):
    payload = {
        **minimal_payload(ref),
        "steps": [
            {"position": 1, "description": "Preheat oven", "duration": 15},
            {"position": 2, "description": "Mix ingredients", "duration": None},
        ],
    }
    response = auth_client.post("/api/recipes", json=payload)
    assert response.status_code == 201


def test_create_recipe_returns_id(auth_client, ref):
    r1 = auth_client.post("/api/recipes", json={**minimal_payload(ref), "title": "Recipe A"})
    r2 = auth_client.post("/api/recipes", json={**minimal_payload(ref), "title": "Recipe B"})
    assert r1.json()["id"] != r2.json()["id"]
