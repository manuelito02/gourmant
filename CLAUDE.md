# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the app
```bash
docker compose up --build -d        # build image and start all services
docker compose up -d                # start without rebuild (uses cached image)
docker compose down -v              # stop and wipe all volumes (resets DB)
docker compose watch                # start with live-sync (app/ and alembic/ synced into container)
```

The app runs at http://localhost:8000. The container entrypoint compiles translations, runs `alembic upgrade head`, then starts uvicorn with `--reload`.

### Tests
Tests require a running PostgreSQL on localhost:5432 (the Docker `db` service). Run from the project root:
```bash
uv run pytest                       # full suite with coverage (must reach 80%)
uv run pytest --no-cov              # skip coverage
uv run pytest tests/test_recipes.py::test_dashboard_filter_by_title   # single test
uv run pytest -q -k "filter"        # keyword filter
```

The test session creates and migrates a separate `gourmant_test` database on each run. The `db` fixture truncates user-created data before and after every test; seeded reference data (ingredients, units, types) is preserved.

### Linting
```bash
uv run ruff check app/ tests/       # lint
uv run ruff check --fix app/ tests/ # auto-fix
```
Line length: 100. Config in `pyproject.toml`.

### Translations
```bash
# Extract new strings from Python and Jinja2 sources
uv run pybabel extract -F babel.cfg -o translations/messages.pot .

# Update existing .po files with new strings
uv run pybabel update -i translations/messages.pot -d translations

# Compile .po → .mo (required after any .po edit)
uv run pybabel compile -d translations
```
The Docker entrypoint also compiles translations on every start (`pybabel compile -d translations -f`), so the container always reflects the checked-in `.po` files. Always commit both `.po` and `.mo` files together.

### Demo recipe seed (optional)
Loads 50 French recipes (from chefsimon.com, pre-scraped) for bob and charly. Run once after the DB is migrated:
```bash
docker compose exec app python -m app.scripts.seed_demo_recipes
```
The dataset lives in `app/scripts/demo_recipes/` (JSON + cached images). To refresh it from the source:
```bash
uv run python -m app.scripts.build_demo_recipes   # overwrites recipes.json + images/
```

### Database migrations
```bash
# Create a new migration
docker compose exec app alembic revision -m "describe_change"

# Apply migrations
docker compose exec app alembic upgrade head
```
Migrations live in `alembic/versions/` numbered `0001_…`, `0002_…`. Seed data (reference tables, demo users) is embedded in the migration that creates those tables.

## Architecture

### Stack
- **FastAPI** with **Starlette** `SessionMiddleware` (signed cookie sessions — Redis is present in docker-compose but not yet used)
- **SQLAlchemy 2.0** ORM (legacy `db.query()` style), **Alembic** migrations
- **Jinja2** server-rendered HTML, one `Jinja2Templates` instance per language cached at import time
- **Babel** for i18n (EN/FR/DE/NL); `app/i18n.py` loads all `.mo` files once at startup

### Request flow
`app/main.py` registers two routers (`auth`, `recipes`) and the static file mount. Session language is stored in `request.session["lang"]` and switched via `POST /set-language`. Page routes raise `HTTPException(302, headers={"location": "/login"})` when unauthenticated (not `RedirectResponse`, because FastAPI dependencies cannot return responses).

### i18n pattern
`get_templates(request)` returns the per-language `Jinja2Templates` instance, giving every template a `_()` function. For server-side string translation outside templates use `gettext_for(request, msgid)`. `_form_context(db, request)` applies `gettext_for` to unit names and ingredient type names before they are JSON-serialised as JS globals (`AMOUNT_UNITS`, `INGREDIENT_TYPES`).

### Data model highlights
- `ingredients.name` is the canonical English name. Translations live in `ingredient_translations (ingredient_id, lang, name)` with a unique constraint on `(ingredient_id, lang)`.
- `Recipe` → `user_id` FK; `Recipe.user` relationship gives the author. Only the author can edit a recipe (`_load_recipe` filters by both `recipe_id` and `user_id`).
- Eager loading: all recipe detail queries use `selectinload` chains to avoid N+1. The dashboard loads `Recipe.type` and `Recipe.user`; the detail/edit pages additionally load steps, ingredients, units, and ingredient groups.
- `RecipeIngredient` rows belong to either the recipe directly (`group_id IS NULL`) or a `RecipeIngredientGroup`. Both paths are rendered in the recipe detail and form templates.

### Test fixtures
`conftest.py` `ref` fixture returns a dict of IDs for the first/last seeded ingredient, first unit, first type, and first ingredient type. `auth_client` is a `TestClient` with a registered+logged-in user. `create_recipe(client, payload)` posts to `/api/recipes` and returns the new ID. `minimal_payload(ref)` returns the smallest valid recipe payload (title + type only, no ingredients or steps required by the schema).
