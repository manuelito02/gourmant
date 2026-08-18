# Gourmant

A recipe management web application — FastAPI, PostgreSQL, and server-rendered Jinja2, running in Docker.

Users write and share recipes with structured ingredients, grouped ingredient sections, ordered work steps
with per-step durations, and images at both recipe and step level. Interface and content are available in
four languages.

---

> ### A note on authorship
>
> **This application was written by Claude (Anthropic's coding agent) under my direction.** I specified the
> requirements and the architecture, reviewed every change, tested the behaviour, and rejected what did not
> work — but I did not hand-write the implementation.
>
> I am stating this plainly because the distinction matters. What this repository demonstrates is
> *specification, architectural direction and code review* of an AI-assisted build, not my own hands-on
> fluency with FastAPI or Redis. It is published as an honest record of that experiment.
>
> Commits authored with agent assistance are tagged `(Claude)` in the git history, so the split is auditable.

---

## Features

### Accounts and permissions
- Registration and login with session-based authentication, sessions signed via `itsdangerous`
- Passwords hashed with **bcrypt**, strength enforced at registration using **zxcvbn**
- **Two roles — user and admin.** Admins reach a user-management panel to view, edit and manage accounts;
  a default admin is seeded on first run
- **Ownership-based authorisation**: any user may read any recipe, but only its author (or an admin) may edit
  or delete it — enforced server-side on every mutating route, not merely hidden in the UI
- Per-user account settings: interface language and password change
- **Rate limiting** on authentication endpoints via `slowapi`, to blunt credential-stuffing attempts

### Recipes
- Create, edit and delete recipes with title, description, type and serving count
- **Structured ingredients** — each entry is a typed reference to an ingredient row plus a numeric amount and
  a unit, rather than a line of free text. This is what makes scaling and translation possible
- **Ingredient groups** — ordered, named sections ("For the dough", "For the filling") within one recipe
- **Ordered work steps** with optional per-step duration in minutes; a database constraint guarantees
  positions stay unique within a recipe
- **Duration computation** — step durations aggregate into a total preparation time for the recipe
- **Serving scaler** — ingredient amounts recompute live against a chosen serving count
- **Image upload** at recipe and step level, processed with Pillow and served from a persistent volume
- **Dietary classification** derived from ingredient composition, surfaced as recipe badges
- Dashboard with text search, type filtering, sorting and pagination

### Internationalisation
- Full interface translation in **English, French, German and Dutch** via Babel
- Ingredient names, amount units and recipe types are translated as *data*, not as interface strings —
  a separate `ingredient_translations` table with cascade rules, so content localises as well as chrome

---

## Data model

PostgreSQL, accessed through SQLAlchemy 2.0's typed `Mapped[]` ORM. Twelve Alembic migrations describe the
schema's full history.

```
users ──< recipes ──< recipe_ingredient_groups ──< recipe_ingredients >── ingredients
                 │                                          │                  │
                 │                                          └──> amount_units  └──< ingredient_translations
                 ├──< steps ──< step_images
                 └──> recipe_types
```

Design points worth noting:

- **Ingredients are first-class rows, not strings.** A recipe ingredient is `(ingredient_id, amount, unit_id)`,
  which is what allows scaling, translation and dietary classification to work at all. Free-text ingredients
  would have made every one of those features impossible.
- **Ingredient groups are optional.** `recipe_ingredients.group_id` is nullable, so a simple recipe needs no
  grouping while a complex one can have several — without a second code path.
- **Ordering is enforced in the database.** `UniqueConstraint(recipe_id, position)` on steps, and the
  equivalent on step images, so ordering cannot silently corrupt through a concurrent write.
- **Amounts use `Numeric(10, 3)`**, not float — quantities are exact, and scaling does not accumulate binary
  rounding error.
- **Cascade rules are explicit.** `all, delete-orphan` on the composition relationships, so removing a recipe
  cannot orphan its steps, ingredients or images.

---

## Testing

```
pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Coverage is gated at 80 % and the suite fails below it.** Test modules cover authentication, account
management, the admin panel, recipes, uploads, internationalisation, and the demo seed data. Fixtures build a
real database per test session rather than mocking the ORM, so the migrations and constraints are exercised
alongside the application code.

Linting and formatting are handled by **ruff**.

---

## Running it

```bash
git clone <repo> && cd gourmant
cp .env.example .env          # set SECRET_KEY, database and Redis credentials
docker compose up --build
```

The stack starts the application, PostgreSQL and Redis. `entrypoint.sh` applies Alembic migrations before the
server accepts traffic, so a fresh database converges to the current schema automatically.

Useful scripts:

| Script | Purpose |
|---|---|
| `scripts/backup.sh` | Dump the database and the uploads volume |
| `scripts/restore.sh` | Restore both from a dump |
| `scripts/public-url.sh` | Expose the local instance through a Cloudflare Tunnel |
| `app/scripts/build_demo_recipes.py` | Seed a demonstration dataset with images |

---

## Stack

| Layer | Choice |
|---|---|
| Web framework | FastAPI |
| Templating | Jinja2 (server-rendered) |
| Database | PostgreSQL via SQLAlchemy 2.0 + psycopg 3 |
| Migrations | Alembic |
| Cache / rate-limit store | Redis |
| Authentication | Session cookies, bcrypt, itsdangerous, zxcvbn |
| Rate limiting | slowapi |
| Images | Pillow |
| i18n | Babel |
| Testing | pytest, pytest-cov (80 % gate), httpx |
| Linting | ruff |
| Runtime | Docker, docker compose |

---

## Licence

Personal project. Not intended for production use as-is.
