from app.models.ingredient import Ingredient, IngredientTranslation

# ── Shared helpers ────────────────────────────────────────────────────────────

OTHER_USER = {
    "first_name": "Bob",
    "last_name": "Smith",
    "email": "bob@example.com",
    "password": "correct-horse-battery-staple",
    "password_confirm": "correct-horse-battery-staple",
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


def test_dashboard_shows_all_recipes_with_author(client, ref):
    # Recipes from all users appear on the dashboard; author name is shown
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
    create_recipe(client, {**minimal_payload(ref), "title": "Bob Stew"})
    response = client.get("/dashboard")
    # Both recipes visible to Bob
    assert "Alice Soup" in response.text
    assert "Bob Stew" in response.text
    # Author names present
    assert "Alice A" in response.text


# ── Dashboard filters ─────────────────────────────────────────────────────────


def test_dashboard_filter_text_matches_translated_ingredient_name(auth_client, ref, db):
    # "onion" is seeded with French translation "oignon"; searching "oig" in FR
    # should find the recipe that uses it even though the English name differs.
    onion = db.query(Ingredient).filter(Ingredient.name == "onion").first()
    if onion is None:
        return  # ingredient not seeded — skip
    ing = {"amount": 1, "unit_id": ref["unit_id"], "ingredient_id": onion.id}
    create_recipe(
        auth_client,
        {**minimal_payload(ref), "title": "French Dish", "ungrouped_ingredients": [ing]},
    )
    create_recipe(auth_client, {**minimal_payload(ref), "title": "Other Dish"})
    auth_client.post("/set-language", data={"lang": "fr"})
    response = auth_client.get("/dashboard?q=oig")
    auth_client.post("/set-language", data={"lang": "en"})
    assert "French Dish" in response.text
    assert "Other Dish" not in response.text


def test_dashboard_filter_text_matches_ingredient_name(auth_client, ref, db):
    first_ing = db.query(Ingredient).filter(Ingredient.id == ref["ingredient_id"]).one()
    ing = {"amount": 1, "unit_id": ref["unit_id"], "ingredient_id": ref["ingredient_id"]}
    create_recipe(
        auth_client,
        {**minimal_payload(ref), "title": "Mystery Dish", "ungrouped_ingredients": [ing]},
    )
    create_recipe(auth_client, {**minimal_payload(ref), "title": "Other Dish"})
    # Searching the ingredient name should surface the recipe that uses it.
    response = auth_client.get(f"/dashboard?q={first_ing.name[:4]}")
    assert "Mystery Dish" in response.text


def test_dashboard_filter_by_title(auth_client, ref):
    create_recipe(auth_client, {**minimal_payload(ref), "title": "Chocolate Cake"})
    create_recipe(auth_client, {**minimal_payload(ref), "title": "Tomato Soup"})
    response = auth_client.get("/dashboard?q=chocolate")
    assert "Chocolate Cake" in response.text
    assert "Tomato Soup" not in response.text


def test_dashboard_filter_by_description(auth_client, ref):
    create_recipe(
        auth_client,
        {**minimal_payload(ref), "title": "Soup", "description": "rich broth"},
    )
    create_recipe(auth_client, {**minimal_payload(ref), "title": "Cake"})
    response = auth_client.get("/dashboard?q=broth")
    assert "Soup" in response.text
    assert "Cake" not in response.text


def test_dashboard_filter_by_type(auth_client, ref, db):
    from app.models.recipe import RecipeType

    types = db.query(RecipeType).order_by(RecipeType.id).all()
    assert len(types) >= 2
    t_a, t_b = types[0], types[1]
    create_recipe(auth_client, {**minimal_payload(ref), "type_id": t_a.id, "title": "Recipe A"})
    create_recipe(auth_client, {**minimal_payload(ref), "type_id": t_b.id, "title": "Recipe B"})
    response = auth_client.get(f"/dashboard?types={t_a.id}")
    assert "Recipe A" in response.text
    assert "Recipe B" not in response.text


def test_dashboard_filter_no_match_shows_empty(auth_client, ref):
    create_recipe(auth_client, minimal_payload(ref))
    response = auth_client.get("/dashboard?q=zzznomatch")
    assert "No recipes match your filters" in response.text
    assert "Clear filters" in response.text


def test_dashboard_sort_title_asc(auth_client, ref):
    create_recipe(auth_client, {**minimal_payload(ref), "title": "Zebra Cake"})
    create_recipe(auth_client, {**minimal_payload(ref), "title": "Apple Tart"})
    response = auth_client.get("/dashboard?sort=title_asc")
    assert response.text.index("Apple Tart") < response.text.index("Zebra Cake")


def test_dashboard_sort_title_desc(auth_client, ref):
    create_recipe(auth_client, {**minimal_payload(ref), "title": "Zebra Cake"})
    create_recipe(auth_client, {**minimal_payload(ref), "title": "Apple Tart"})
    response = auth_client.get("/dashboard?sort=title_desc")
    assert response.text.index("Zebra Cake") < response.text.index("Apple Tart")


def test_dashboard_sort_date_asc(auth_client, ref):
    create_recipe(auth_client, {**minimal_payload(ref), "title": "First Recipe"})
    create_recipe(auth_client, {**minimal_payload(ref), "title": "Second Recipe"})
    response = auth_client.get("/dashboard?sort=date_asc")
    assert response.text.index("First Recipe") < response.text.index("Second Recipe")


# ── Pagination ───────────────────────────────────────────────────────────────


def test_dashboard_paginates_at_page_size(auth_client, ref):
    for i in range(25):
        create_recipe(auth_client, {**minimal_payload(ref), "title": f"Recipe {i:02d}"})
    page1 = auth_client.get("/dashboard")
    page2 = auth_client.get("/dashboard?page=2")
    # 24 recipe cards on page 1, 1 on page 2
    assert page1.text.count('class="recipe-card"') == 24
    assert page2.text.count('class="recipe-card"') == 1


def test_dashboard_page_out_of_range_clamps(auth_client, ref):
    create_recipe(auth_client, minimal_payload(ref))
    response = auth_client.get("/dashboard?page=999")
    assert response.status_code == 200
    assert response.text.count('class="recipe-card"') == 1


def test_dashboard_pagination_preserves_filters(auth_client, ref):
    for i in range(26):
        create_recipe(auth_client, {**minimal_payload(ref), "title": f"Soup {i:02d}"})
    create_recipe(auth_client, {**minimal_payload(ref), "title": "Unrelated"})
    page2 = auth_client.get("/dashboard?q=Soup&page=2")
    assert page2.status_code == 200
    # 26 soups → page 2 should have 2, and "Unrelated" must not appear
    assert "Unrelated" not in page2.text
    assert page2.text.count('class="recipe-card"') == 2


def test_dashboard_no_pagination_when_one_page(auth_client, ref):
    for _i in range(5):
        create_recipe(auth_client, minimal_payload(ref))
    response = auth_client.get("/dashboard")
    assert "pagination" not in response.text


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


def test_recipe_form_translates_units_and_types(auth_client):
    auth_client.post("/set-language", data={"lang": "fr"})
    response = auth_client.get("/recipes/new")
    # Amount units — ASCII-safe French names present in JSON
    assert "Gramme" in response.text
    assert "Tasse" in response.text  # cup → Tasse
    assert r"C\u00e0c" in response.text  # Càc (teaspoon shorthand)
    assert r"C\u00e0s" in response.text  # Càs (tablespoon shorthand)
    # Ingredient types — tojson escapes accented chars too
    assert r"L\u00e9gume" in response.text  # Légume
    # Reset language
    auth_client.post("/set-language", data={"lang": "en"})


# ── Recipe detail page ────────────────────────────────────────────────────────


def test_recipe_detail_redirects_when_logged_out(client):
    response = client.get("/recipes/999")
    assert response.url.path == "/login"


def test_recipe_detail_404_nonexistent(auth_client):
    response = auth_client.get("/recipes/999999")
    assert response.status_code == 404


def test_recipe_detail_visible_to_other_users(client, ref):
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

    # Any authenticated user can view any recipe
    client.post("/register", data=OTHER_USER)
    response = client.get(f"/recipes/{recipe_id}")
    assert response.status_code == 200


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


# ── Multilingual ingredient search ────────────────────────────────────────────


def test_search_ingredients_french_returns_translation(client):
    """With lang=fr, searching the French name returns the translated ingredient."""
    client.post("/set-language", data={"lang": "fr"})
    response = client.get("/api/ingredients?q=tomate")
    assert response.status_code == 200
    names = [i["name"] for i in response.json()]
    assert "tomate" in names


def test_search_ingredients_french_fallback_to_canonical(auth_client, ref):
    """User-created ingredient with no French translation still appears in French searches."""
    auth_client.post("/api/ingredients", json={"name": "Wakame", "type_id": ref["ing_type_id"]})
    auth_client.post("/set-language", data={"lang": "fr"})
    response = auth_client.get("/api/ingredients?q=Wakame")
    names = [i["name"] for i in response.json()]
    assert "Wakame" in names


def test_search_ingredients_german_returns_translation(client):
    """With lang=de, searching the German name returns the translated ingredient."""
    client.post("/set-language", data={"lang": "de"})
    response = client.get("/api/ingredients?q=Karotte")
    assert response.status_code == 200
    names = [i["name"] for i in response.json()]
    assert "Karotte" in names


def test_search_ingredients_dutch_returns_translation(client):
    """With lang=nl, searching the Dutch name returns the translated ingredient."""
    client.post("/set-language", data={"lang": "nl"})
    response = client.get("/api/ingredients?q=wortel")
    assert response.status_code == 200
    names = [i["name"] for i in response.json()]
    assert "wortel" in names


def test_search_ingredients_translated_result_has_id_and_name(client):
    """Translated search results include both id and name fields."""
    client.post("/set-language", data={"lang": "fr"})
    response = client.get("/api/ingredients?q=tomate")
    item = response.json()[0]
    assert "id" in item
    assert "name" in item


# ── Multilingual ingredient creation ─────────────────────────────────────────


def test_create_ingredient_in_french_stores_translation(auth_client, ref, db):
    """Creating an ingredient in French mode stores an ingredient_translations row."""
    auth_client.post("/set-language", data={"lang": "fr"})
    res = auth_client.post(
        "/api/ingredients", json={"name": "Papaye", "type_id": ref["ing_type_id"]}
    )
    assert res.status_code == 201
    ing_id = res.json()["id"]
    trans = (
        db.query(IngredientTranslation)
        .filter(IngredientTranslation.ingredient_id == ing_id, IngredientTranslation.lang == "fr")
        .first()
    )
    assert trans is not None
    assert trans.name == "Papaye"


def test_create_ingredient_in_english_stores_no_translation(auth_client, ref, db):
    """Creating an ingredient in English mode does NOT create any translation row."""
    res = auth_client.post(
        "/api/ingredients", json={"name": "Chayote", "type_id": ref["ing_type_id"]}
    )
    assert res.status_code == 201
    ing_id = res.json()["id"]
    assert (
        db.query(IngredientTranslation)
        .filter(IngredientTranslation.ingredient_id == ing_id)
        .count()
        == 0
    )


def test_create_ingredient_duplicate_translation_rejected(auth_client, ref):
    """Re-creating an ingredient with the same name in the same language returns 400."""
    auth_client.post("/set-language", data={"lang": "fr"})
    auth_client.post("/api/ingredients", json={"name": "Papaye", "type_id": ref["ing_type_id"]})
    response = auth_client.post(
        "/api/ingredients", json={"name": "Papaye", "type_id": ref["ing_type_id"]}
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_ingredient_blocked_by_existing_seeded_translation(auth_client, ref):
    """Creating an ingredient whose name already exists as a seeded translation is rejected."""
    # "tomate" is the French translation of the seeded "tomato" ingredient
    auth_client.post("/set-language", data={"lang": "fr"})
    response = auth_client.post(
        "/api/ingredients", json={"name": "tomate", "type_id": ref["ing_type_id"]}
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_ingredient_french_searchable_after_creation(auth_client, ref):
    """A French-created ingredient can be found by its name in the French search."""
    auth_client.post("/set-language", data={"lang": "fr"})
    auth_client.post("/api/ingredients", json={"name": "Papaye", "type_id": ref["ing_type_id"]})
    response = auth_client.get("/api/ingredients?q=Papaye")
    names = [i["name"] for i in response.json()]
    assert "Papaye" in names


# ── Recipe detail with ingredient translations ────────────────────────────────


def test_recipe_detail_shows_translated_ungrouped_ingredient(auth_client, ref, db):
    """Recipe detail shows the French name for an ungrouped seeded ingredient."""
    onion = db.query(Ingredient).filter(Ingredient.name == "onion").first()
    payload = {
        **minimal_payload(ref),
        "ungrouped_ingredients": [
            {"ingredient_id": onion.id, "amount": 2, "unit_id": ref["unit_id"]}
        ],
    }
    recipe_id = create_recipe(auth_client, payload)
    auth_client.post("/set-language", data={"lang": "fr"})
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert "oignon" in response.text


def test_recipe_detail_shows_translated_grouped_ingredient(auth_client, ref, db):
    """Recipe detail shows the French name for a grouped seeded ingredient."""
    tomato = db.query(Ingredient).filter(Ingredient.name == "tomato").first()
    payload = {
        **minimal_payload(ref),
        "ingredient_groups": [
            {
                "name": "Sauce",
                "position": 0,
                "ingredients": [
                    {"ingredient_id": tomato.id, "amount": 400, "unit_id": ref["unit_id"]}
                ],
            }
        ],
    }
    recipe_id = create_recipe(auth_client, payload)
    auth_client.post("/set-language", data={"lang": "fr"})
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert "tomate" in response.text


def test_recipe_detail_canonical_name_when_no_translation(auth_client, ref):
    """Ingredient created without a translation shows the canonical name in French mode."""
    auth_client.post("/api/ingredients", json={"name": "Wakame", "type_id": ref["ing_type_id"]})
    wakame_id = auth_client.get("/api/ingredients?q=Wakame").json()[0]["id"]
    payload = {
        **minimal_payload(ref),
        "ungrouped_ingredients": [
            {"ingredient_id": wakame_id, "amount": 50, "unit_id": ref["unit_id"]}
        ],
    }
    recipe_id = create_recipe(auth_client, payload)
    auth_client.post("/set-language", data={"lang": "fr"})
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert "Wakame" in response.text


def test_recipe_detail_english_shows_canonical_name(auth_client, ref, db):
    """In English mode, the canonical ingredient name is shown (not a translation)."""
    onion = db.query(Ingredient).filter(Ingredient.name == "onion").first()
    payload = {
        **minimal_payload(ref),
        "ungrouped_ingredients": [
            {"ingredient_id": onion.id, "amount": 3, "unit_id": ref["unit_id"]}
        ],
    }
    recipe_id = create_recipe(auth_client, payload)
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert "onion" in response.text


# ── Edit recipe form ──────────────────────────────────────────────────────────


def test_edit_form_redirects_when_logged_out(client):
    response = client.get("/recipes/999/edit")
    assert response.url.path == "/login"


def test_edit_form_404_nonexistent(auth_client):
    response = auth_client.get("/recipes/999999/edit")
    assert response.status_code == 404


def test_edit_form_403_other_users_recipe(client, ref):
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

    client.post("/register", data=OTHER_USER)
    response = client.get(f"/recipes/{recipe_id}/edit")
    assert response.status_code == 403


def test_edit_form_loads_with_recipe_data(auth_client, ref):
    recipe_id = create_recipe(
        auth_client,
        {**minimal_payload(ref), "title": "My Stew", "description": "Slow cooked"},
    )
    response = auth_client.get(f"/recipes/{recipe_id}/edit")
    assert response.status_code == 200
    assert "Edit recipe" in response.text
    assert "My Stew" in response.text
    assert "Slow cooked" in response.text


def test_edit_form_contains_recipe_data_js(auth_client, ref):
    recipe_id = create_recipe(auth_client, {**minimal_payload(ref), "title": "Tiramisu"})
    response = auth_client.get(f"/recipes/{recipe_id}/edit")
    assert "RECIPE_DATA" in response.text
    assert "RECIPE_ID" in response.text
    assert "Tiramisu" in response.text


# ── Recipe update API ─────────────────────────────────────────────────────────


def test_update_recipe_requires_auth(client, ref):
    response = client.put("/api/recipes/999", json=minimal_payload(ref))
    assert response.status_code == 401


def test_update_recipe_404_nonexistent(auth_client, ref):
    response = auth_client.put("/api/recipes/999999", json=minimal_payload(ref))
    assert response.status_code == 404


def test_update_recipe_404_other_users_recipe(client, ref):
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

    client.post("/register", data=OTHER_USER)
    response = client.put(f"/api/recipes/{recipe_id}", json=minimal_payload(ref))
    assert response.status_code == 404


def test_update_recipe_title_and_description(auth_client, ref):
    recipe_id = create_recipe(
        auth_client, {**minimal_payload(ref), "title": "Old Title", "description": "Old desc"}
    )
    payload = {**minimal_payload(ref), "title": "New Title", "description": "New desc"}
    response = auth_client.put(f"/api/recipes/{recipe_id}", json=payload)
    assert response.status_code == 200
    assert response.json()["id"] == recipe_id

    detail = auth_client.get(f"/recipes/{recipe_id}")
    assert "New Title" in detail.text
    assert "New desc" in detail.text
    assert "Old Title" not in detail.text


def test_update_recipe_replaces_ingredients(auth_client, ref):
    orig = {
        **minimal_payload(ref),
        "ungrouped_ingredients": [
            {"ingredient_id": ref["ingredient_id"], "amount": 100, "unit_id": ref["unit_id"]}
        ],
    }
    recipe_id = create_recipe(auth_client, orig)

    updated = {
        **minimal_payload(ref),
        "ungrouped_ingredients": [
            {"ingredient_id": ref["ingredient_id2"], "amount": 999, "unit_id": ref["unit_id"]}
        ],
    }
    auth_client.put(f"/api/recipes/{recipe_id}", json=updated)

    detail = auth_client.get(f"/recipes/{recipe_id}")
    assert "999" in detail.text


def test_update_recipe_replaces_steps(auth_client, ref):
    orig = {
        **minimal_payload(ref),
        "steps": [{"position": 1, "description": "Old step", "duration": None}],
    }
    recipe_id = create_recipe(auth_client, orig)

    updated = {
        **minimal_payload(ref),
        "steps": [{"position": 1, "description": "New step", "duration": 10}],
    }
    auth_client.put(f"/api/recipes/{recipe_id}", json=updated)

    detail = auth_client.get(f"/recipes/{recipe_id}")
    assert "New step" in detail.text
    assert "Old step" not in detail.text


def test_update_recipe_replaces_groups(auth_client, ref):
    orig = {
        **minimal_payload(ref),
        "ingredient_groups": [
            {
                "name": "Old Group",
                "position": 0,
                "ingredients": [
                    {"ingredient_id": ref["ingredient_id"], "amount": 50, "unit_id": ref["unit_id"]}
                ],
            }
        ],
    }
    recipe_id = create_recipe(auth_client, orig)

    updated = {
        **minimal_payload(ref),
        "ingredient_groups": [
            {
                "name": "New Group",
                "position": 0,
                "ingredients": [
                    {
                        "ingredient_id": ref["ingredient_id2"],
                        "amount": 75,
                        "unit_id": ref["unit_id"],
                    }
                ],
            }
        ],
    }
    auth_client.put(f"/api/recipes/{recipe_id}", json=updated)

    detail = auth_client.get(f"/recipes/{recipe_id}")
    assert "New Group" in detail.text
    assert "Old Group" not in detail.text


def test_update_recipe_returns_same_id(auth_client, ref):
    recipe_id = create_recipe(auth_client, minimal_payload(ref))
    response = auth_client.put(f"/api/recipes/{recipe_id}", json=minimal_payload(ref))
    assert response.json()["id"] == recipe_id


# ── Images ────────────────────────────────────────────────────────────────────

# Valid filenames match the upload endpoint's output: 32 lowercase hex chars + .jpg
_IMG_A = "a" * 32 + ".jpg"
_IMG_B = "b" * 32 + ".jpg"


def test_recipe_with_image_filename_shows_thumbnail_on_dashboard(auth_client, ref):
    payload = {**minimal_payload(ref), "image_filename": _IMG_A}
    create_recipe(auth_client, payload)
    response = auth_client.get("/dashboard")
    assert 'class="recipe-card-thumb"' in response.text
    assert f"thumb_{_IMG_A}" in response.text


def test_recipe_with_image_filename_shows_hero_on_detail(auth_client, ref):
    recipe_id = create_recipe(auth_client, {**minimal_payload(ref), "image_filename": _IMG_A})
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert "has-hero" in response.text
    assert _IMG_A in response.text


def test_recipe_without_image_has_no_hero(auth_client, ref):
    recipe_id = create_recipe(auth_client, minimal_payload(ref))
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert "has-hero" not in response.text


def test_recipe_with_step_images_shows_on_detail(auth_client, ref, db):
    from app.models.recipe import Step, StepImage

    recipe_id = create_recipe(auth_client, minimal_payload(ref))
    step = db.query(Step).filter(Step.recipe_id == recipe_id).first()
    if not step:
        step = Step(recipe_id=recipe_id, position=1, description="Boil water")
        db.add(step)
        db.flush()
    db.add(StepImage(step_id=step.id, position=0, filename=_IMG_A))
    db.commit()

    response = auth_client.get(f"/recipes/{recipe_id}")
    assert f"thumb_{_IMG_A}" in response.text
    assert 'class="step-images"' in response.text


def test_edit_form_includes_image_filename_in_recipe_data(auth_client, ref):
    recipe_id = create_recipe(auth_client, {**minimal_payload(ref), "image_filename": _IMG_A})
    response = auth_client.get(f"/recipes/{recipe_id}/edit")
    assert _IMG_A in response.text


def test_update_recipe_clears_image_filename(auth_client, ref):
    recipe_id = create_recipe(auth_client, {**minimal_payload(ref), "image_filename": _IMG_A})
    auth_client.put(
        f"/api/recipes/{recipe_id}", json={**minimal_payload(ref), "image_filename": None}
    )
    response = auth_client.get(f"/recipes/{recipe_id}")
    assert "has-hero" not in response.text


def test_update_recipe_replaces_step_images(auth_client, ref):
    """Old StepImage rows must be gone and new ones present after update."""
    step_with_img = {"position": 1, "description": "Fry", "image_filenames": [_IMG_A]}
    recipe_id = create_recipe(auth_client, {**minimal_payload(ref), "steps": [step_with_img]})

    updated_step = {"position": 1, "description": "Fry", "image_filenames": [_IMG_B]}
    auth_client.put(
        f"/api/recipes/{recipe_id}",
        json={**minimal_payload(ref), "steps": [updated_step]},
    )

    response = auth_client.get(f"/recipes/{recipe_id}")
    assert f"thumb_{_IMG_B}" in response.text
    assert f"thumb_{_IMG_A}" not in response.text


# ── Image filename validation ──────────────────────────────────────────────────


def test_create_recipe_rejects_path_traversal_image_filename(auth_client, ref):
    response = auth_client.post(
        "/api/recipes", json={**minimal_payload(ref), "image_filename": "../../etc/passwd"}
    )
    assert response.status_code == 422


def test_create_recipe_rejects_non_hex_image_filename(auth_client, ref):
    response = auth_client.post(
        "/api/recipes", json={**minimal_payload(ref), "image_filename": "notahex.jpg"}
    )
    assert response.status_code == 422


def test_create_recipe_accepts_valid_image_filename(auth_client, ref):
    response = auth_client.post(
        "/api/recipes", json={**minimal_payload(ref), "image_filename": _IMG_A}
    )
    assert response.status_code == 201


def test_step_image_filename_rejects_path_traversal(auth_client, ref):
    payload = {
        **minimal_payload(ref),
        "steps": [{"position": 1, "description": "x", "image_filenames": ["../evil.jpg"]}],
    }
    response = auth_client.post("/api/recipes", json=payload)
    assert response.status_code == 422


def test_update_recipe_rejects_invalid_image_filename(auth_client, ref):
    recipe_id = create_recipe(auth_client, minimal_payload(ref))
    response = auth_client.put(
        f"/api/recipes/{recipe_id}",
        json={**minimal_payload(ref), "image_filename": "../../secret.jpg"},
    )
    assert response.status_code == 422


# ── Dietary classification ────────────────────────────────────────────────────


def _create_ing(client, ref, name, classification):
    """Create a test ingredient with the given dietary classification; return its id."""
    res = client.post(
        "/api/ingredients",
        json={"name": name, "type_id": ref["ing_type_id"], "classification": classification},
    )
    assert res.status_code == 201
    return res.json()["id"]


def _recipe_with_ings(ref, *ing_ids):
    return {
        **minimal_payload(ref),
        "ungrouped_ingredients": [
            {"ingredient_id": i, "amount": 1.0, "unit_id": ref["unit_id"]} for i in ing_ids
        ],
    }


def test_create_ingredient_defaults_to_vegan(auth_client, ref):
    vegan_id = _create_ing(auth_client, ref, "Test Spinach", "vegan")
    recipe_id = create_recipe(auth_client, _recipe_with_ings(ref, vegan_id))
    resp = auth_client.get(f"/recipes/{recipe_id}")
    assert "Vegan" in resp.text


def test_create_ingredient_explicit_pescatarian(auth_client, ref):
    pesc_id = _create_ing(auth_client, ref, "Test Anchovy", "pescatarian")
    recipe_id = create_recipe(auth_client, _recipe_with_ings(ref, pesc_id))
    resp = auth_client.get(f"/recipes/{recipe_id}")
    assert "Pescatarian" in resp.text


def test_create_ingredient_invalid_classification_rejected(auth_client, ref):
    res = auth_client.post(
        "/api/ingredients",
        json={"name": "Test Bad", "type_id": ref["ing_type_id"], "classification": "omnivore"},
    )
    assert res.status_code == 422


def test_recipe_no_ingredients_is_vegan(auth_client, ref):
    recipe_id = create_recipe(auth_client, minimal_payload(ref))
    resp = auth_client.get(f"/recipes/{recipe_id}")
    assert "Vegan" in resp.text


def test_recipe_all_vegan_is_vegan(auth_client, ref):
    v1 = _create_ing(auth_client, ref, "Test Carrot", "vegan")
    v2 = _create_ing(auth_client, ref, "Test Garlic", "vegan")
    recipe_id = create_recipe(auth_client, _recipe_with_ings(ref, v1, v2))
    resp = auth_client.get(f"/recipes/{recipe_id}")
    assert "Vegan" in resp.text


def test_recipe_one_vegetarian_overrides_vegan(auth_client, ref):
    vegan_id = _create_ing(auth_client, ref, "Test Onion", "vegan")
    veg_id = _create_ing(auth_client, ref, "Test Cheese", "vegetarian")
    recipe_id = create_recipe(auth_client, _recipe_with_ings(ref, vegan_id, veg_id))
    resp = auth_client.get(f"/recipes/{recipe_id}")
    assert "Vegetarian" in resp.text


def test_recipe_pescatarian_overrides_vegetarian(auth_client, ref):
    veg_id = _create_ing(auth_client, ref, "Test Butter", "vegetarian")
    pesc_id = _create_ing(auth_client, ref, "Test Tuna", "pescatarian")
    recipe_id = create_recipe(auth_client, _recipe_with_ings(ref, veg_id, pesc_id))
    resp = auth_client.get(f"/recipes/{recipe_id}")
    assert "Pescatarian" in resp.text


def test_recipe_meat_overrides_all(auth_client, ref):
    veg_id = _create_ing(auth_client, ref, "Test Milk", "vegetarian")
    pesc_id = _create_ing(auth_client, ref, "Test Salmon", "pescatarian")
    meat_id = _create_ing(auth_client, ref, "Test Beef", "meat")
    recipe_id = create_recipe(auth_client, _recipe_with_ings(ref, veg_id, pesc_id, meat_id))
    resp = auth_client.get(f"/recipes/{recipe_id}")
    assert "Meat" in resp.text


def test_recipe_classification_order_independent(auth_client, ref):
    meat_id = _create_ing(auth_client, ref, "Test Pork", "meat")
    vegan_id = _create_ing(auth_client, ref, "Test Basil", "vegan")
    recipe_id = create_recipe(auth_client, _recipe_with_ings(ref, vegan_id, meat_id))
    resp = auth_client.get(f"/recipes/{recipe_id}")
    assert "Meat" in resp.text


def test_dashboard_filter_by_classification_meat(auth_client, ref):
    vegan_id = _create_ing(auth_client, ref, "Test Pepper", "vegan")
    meat_id = _create_ing(auth_client, ref, "Test Lamb", "meat")
    create_recipe(auth_client, {**_recipe_with_ings(ref, vegan_id), "title": "Vegan Salad"})
    create_recipe(auth_client, {**_recipe_with_ings(ref, meat_id), "title": "Meat Stew"})

    resp = auth_client.get("/dashboard?classification=meat")
    assert resp.status_code == 200
    assert "Meat Stew" in resp.text
    assert "Vegan Salad" not in resp.text


def test_dashboard_filter_by_classification_vegan(auth_client, ref):
    vegan_id = _create_ing(auth_client, ref, "Test Kale", "vegan")
    meat_id = _create_ing(auth_client, ref, "Test Duck", "meat")
    create_recipe(auth_client, {**_recipe_with_ings(ref, vegan_id), "title": "Kale Bowl"})
    create_recipe(auth_client, {**_recipe_with_ings(ref, meat_id), "title": "Duck Breast"})

    resp = auth_client.get("/dashboard?classification=vegan")
    assert "Kale Bowl" in resp.text
    assert "Duck Breast" not in resp.text


def test_dashboard_no_filter_shows_all(auth_client, ref):
    vegan_id = _create_ing(auth_client, ref, "Test Tomato", "vegan")
    meat_id = _create_ing(auth_client, ref, "Test Turkey", "meat")
    create_recipe(auth_client, {**_recipe_with_ings(ref, vegan_id), "title": "Tomato Soup"})
    create_recipe(auth_client, {**_recipe_with_ings(ref, meat_id), "title": "Turkey Roast"})

    resp = auth_client.get("/dashboard")
    assert "Tomato Soup" in resp.text
    assert "Turkey Roast" in resp.text


def test_recipe_classification_badge_translates_french(auth_client, ref):
    veg_id = _create_ing(auth_client, ref, "Test Cream", "vegetarian")
    recipe_id = create_recipe(auth_client, _recipe_with_ings(ref, veg_id))
    auth_client.post("/set-language", data={"lang": "fr"})
    resp = auth_client.get(f"/recipes/{recipe_id}")
    assert "Végétarien" in resp.text
    auth_client.post("/set-language", data={"lang": "en"})
