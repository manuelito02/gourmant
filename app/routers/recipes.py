from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased, selectinload

from app.database import get_db
from app.i18n import get_lang, get_templates, gettext_for
from app.models.ingredient import Ingredient, IngredientTranslation, IngredientType
from app.models.recipe import (
    AmountUnit,
    Recipe,
    RecipeIngredient,
    RecipeIngredientGroup,
    RecipeType,
    Step,
)
from app.schemas.recipe import IngredientCreate, RecipeCreate

router = APIRouter()


# ── Auth helpers ──────────────────────────────────────────────────────────────


def _require_user(request: Request) -> int:
    """API routes: raise 401 if not authenticated."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail=gettext_for(request, "Not authenticated"))
    return user_id


def _require_page_user(request: Request) -> int:
    """Page routes: redirect to /login if not authenticated."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=302, detail="Not authenticated", headers={"location": "/login"}
        )
    return user_id


# ── Query helpers ─────────────────────────────────────────────────────────────


def _form_context(db: Session, request: Request) -> dict:
    """Shared context dict for the new/edit recipe form."""
    return {
        "recipe_types": db.query(RecipeType).order_by(RecipeType.name).all(),
        "amount_units": [
            {
                "id": u.id,
                "name": gettext_for(request, u.name),
                "abbreviation": u.abbreviation,
            }
            for u in db.query(AmountUnit).all()
        ],
        "ingredient_types": [
            {"id": t.id, "name": gettext_for(request, t.name)}
            for t in db.query(IngredientType).order_by(IngredientType.name).all()
        ],
    }


def _get_ingredient_translations(
    db: Session, lang: str, ing_ids: list[int]
) -> dict[int, str]:
    """Return {ingredient_id: translated_name} for the given ids and language."""
    if lang == "en" or not ing_ids:
        return {}
    rows = (
        db.query(IngredientTranslation)
        .filter(
            IngredientTranslation.ingredient_id.in_(ing_ids),
            IngredientTranslation.lang == lang,
        )
        .all()
    )
    return {t.ingredient_id: t.name for t in rows}


def _load_recipe(db: Session, recipe_id: int, user_id: int) -> Recipe | None:
    """Fetch a recipe with all relationships eagerly loaded in a fixed number of queries."""
    _ri_opts = [
        selectinload(RecipeIngredient.ingredient),
        selectinload(RecipeIngredient.unit),
    ]
    return (
        db.query(Recipe)
        .options(
            selectinload(Recipe.type),
            selectinload(Recipe.steps),
            selectinload(Recipe.ingredients).options(*_ri_opts),
            selectinload(Recipe.ingredient_groups)
            .selectinload(RecipeIngredientGroup.ingredients)
            .options(*_ri_opts),
        )
        .filter(Recipe.id == recipe_id, Recipe.user_id == user_id)
        .first()
    )


def _populate_recipe(db: Session, recipe_id: int, data: RecipeCreate) -> None:
    """Insert ungrouped ingredients, ingredient groups, and steps for a recipe."""
    for ing in data.ungrouped_ingredients:
        db.add(
            RecipeIngredient(
                recipe_id=recipe_id,
                ingredient_id=ing.ingredient_id,
                amount=ing.amount,
                unit_id=ing.unit_id,
            )
        )
    for group_data in data.ingredient_groups:
        group = RecipeIngredientGroup(
            recipe_id=recipe_id,
            name=group_data.name,
            position=group_data.position,
        )
        db.add(group)
        db.flush()
        for ing in group_data.ingredients:
            db.add(
                RecipeIngredient(
                    recipe_id=recipe_id,
                    ingredient_id=ing.ingredient_id,
                    amount=ing.amount,
                    unit_id=ing.unit_id,
                    group_id=group.id,
                )
            )
    for step in data.steps:
        db.add(
            Step(
                recipe_id=recipe_id,
                position=step.position,
                description=step.description,
                duration=step.duration,
            )
        )


# ── Pages ─────────────────────────────────────────────────────────────────────


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user_id = _require_page_user(request)
    recipes = (
        db.query(Recipe).filter(Recipe.user_id == user_id).order_by(Recipe.created_at.desc()).all()
    )
    return get_templates(request).TemplateResponse(request, "dashboard.html", {"recipes": recipes})


@router.get("/recipes/new", response_class=HTMLResponse)
def new_recipe_form(request: Request, db: Session = Depends(get_db)):
    _require_page_user(request)
    return get_templates(request).TemplateResponse(
        request, "recipe_form.html", _form_context(db, request)
    )


@router.get("/recipes/{recipe_id}/edit", response_class=HTMLResponse)
def edit_recipe_form(recipe_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = _require_page_user(request)
    recipe = _load_recipe(db, recipe_id, user_id)
    if not recipe:
        raise HTTPException(status_code=404, detail=gettext_for(request, "Recipe not found"))

    lang = get_lang(request)
    ing_ids = [ri.ingredient_id for ri in recipe.ingredients]
    translations = _get_ingredient_translations(db, lang, ing_ids)

    recipe_data = {
        "title": recipe.title,
        "description": recipe.description,
        "type_id": recipe.type_id,
        "servings": recipe.servings,
        "ungrouped_ingredients": [
            {
                "ingredient_id": ri.ingredient_id,
                "ingredient_name": translations.get(ri.ingredient_id, ri.ingredient.name),
                "amount": float(ri.amount),
                "unit_id": ri.unit_id,
            }
            for ri in recipe.ingredients
            if ri.group_id is None
        ],
        "ingredient_groups": [
            {
                "name": group.name,
                "position": group.position,
                "ingredients": [
                    {
                        "ingredient_id": ri.ingredient_id,
                        "ingredient_name": translations.get(
                            ri.ingredient_id, ri.ingredient.name
                        ),
                        "amount": float(ri.amount),
                        "unit_id": ri.unit_id,
                    }
                    for ri in group.ingredients
                ],
            }
            for group in recipe.ingredient_groups
        ],
        "steps": [
            {
                "position": step.position,
                "description": step.description,
                "duration": step.duration,
            }
            for step in recipe.steps
        ],
    }

    return get_templates(request).TemplateResponse(
        request,
        "recipe_form.html",
        {
            **_form_context(db, request),
            "edit_mode": True,
            "recipe_id": recipe_id,
            "recipe_data": recipe_data,
        },
    )


@router.get("/recipes/{recipe_id}", response_class=HTMLResponse)
def recipe_detail(recipe_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = _require_page_user(request)
    recipe = _load_recipe(db, recipe_id, user_id)
    if not recipe:
        raise HTTPException(status_code=404, detail=gettext_for(request, "Recipe not found"))

    lang = get_lang(request)
    ing_ids = [ri.ingredient_id for ri in recipe.ingredients]
    translations = _get_ingredient_translations(db, lang, ing_ids)

    return get_templates(request).TemplateResponse(
        request, "recipe_detail.html", {"recipe": recipe, "ingredient_translations": translations}
    )


# ── Ingredient API ────────────────────────────────────────────────────────────


@router.get("/api/ingredients")
def search_ingredients(request: Request, q: str = "", db: Session = Depends(get_db)):
    lang = get_lang(request)
    if lang == "en":
        results = (
            db.query(Ingredient.id, Ingredient.name.label("display_name"))
            .filter(Ingredient.name.ilike(f"%{q}%"))
            .order_by(Ingredient.name)
            .limit(20)
            .all()
        )
    else:
        trans_alias = aliased(IngredientTranslation)
        display = func.coalesce(trans_alias.name, Ingredient.name).label("display_name")
        results = (
            db.query(Ingredient.id, display)
            .outerjoin(
                trans_alias,
                (trans_alias.ingredient_id == Ingredient.id) & (trans_alias.lang == lang),
            )
            .filter(display.ilike(f"%{q}%"))
            .order_by(display)
            .limit(20)
            .all()
        )
    return [{"id": r.id, "name": r.display_name} for r in results]


@router.post("/api/ingredients", status_code=201)
def create_ingredient(data: IngredientCreate, request: Request, db: Session = Depends(get_db)):
    _require_user(request)
    lang = get_lang(request)
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    if db.query(Ingredient).filter(Ingredient.name.ilike(name)).first():
        raise HTTPException(status_code=400, detail="Ingredient already exists")
    if (
        lang != "en"
        and db.query(IngredientTranslation)
        .filter(
            IngredientTranslation.name.ilike(name),
            IngredientTranslation.lang == lang,
        )
        .first()
    ):
        raise HTTPException(status_code=400, detail="Ingredient already exists")
    ing = Ingredient(name=name, type_id=data.type_id)
    db.add(ing)
    db.flush()
    if lang != "en":
        db.add(IngredientTranslation(ingredient_id=ing.id, lang=lang, name=name))
    db.commit()
    db.refresh(ing)
    return {"id": ing.id, "name": ing.name}


# ── Recipe API ────────────────────────────────────────────────────────────────


@router.put("/api/recipes/{recipe_id}")
def update_recipe(
    recipe_id: int, data: RecipeCreate, request: Request, db: Session = Depends(get_db)
):
    user_id = _require_user(request)
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id, Recipe.user_id == user_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail=gettext_for(request, "Recipe not found"))

    recipe.title = data.title.strip()
    recipe.description = data.description
    recipe.type_id = data.type_id
    recipe.servings = data.servings

    # Delete children in FK-safe order before repopulating
    db.query(RecipeIngredient).filter(RecipeIngredient.recipe_id == recipe_id).delete()
    db.query(RecipeIngredientGroup).filter(RecipeIngredientGroup.recipe_id == recipe_id).delete()
    db.query(Step).filter(Step.recipe_id == recipe_id).delete()
    db.flush()

    _populate_recipe(db, recipe.id, data)
    db.commit()
    return {"id": recipe.id}


@router.post("/api/recipes", status_code=201)
def create_recipe(data: RecipeCreate, request: Request, db: Session = Depends(get_db)):
    user_id = _require_user(request)

    recipe = Recipe(
        user_id=user_id,
        title=data.title.strip(),
        description=data.description,
        type_id=data.type_id,
        servings=data.servings,
    )
    db.add(recipe)
    db.flush()

    _populate_recipe(db, recipe.id, data)
    db.commit()
    return {"id": recipe.id}
