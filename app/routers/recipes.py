from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

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


def _require_user(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail=gettext_for(request, "Not authenticated"))
    return user_id


# ── Pages ─────────────────────────────────────────────────────────────────────


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=302)
    user_id = request.session["user_id"]
    recipes = (
        db.query(Recipe).filter(Recipe.user_id == user_id).order_by(Recipe.created_at.desc()).all()
    )
    return get_templates(request).TemplateResponse(request, "dashboard.html", {"recipes": recipes})


@router.get("/recipes/new", response_class=HTMLResponse)
def new_recipe_form(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=302)
    recipe_types = db.query(RecipeType).order_by(RecipeType.name).all()
    amount_units = db.query(AmountUnit).all()
    ingredient_types = db.query(IngredientType).order_by(IngredientType.name).all()
    return get_templates(request).TemplateResponse(
        request,
        "recipe_form.html",
        {
            "recipe_types": recipe_types,
            "amount_units": [
                {"id": u.id, "name": u.name, "abbreviation": u.abbreviation} for u in amount_units
            ],
            "ingredient_types": [{"id": t.id, "name": t.name} for t in ingredient_types],
        },
    )


@router.get("/recipes/{recipe_id}", response_class=HTMLResponse)
def recipe_detail(recipe_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=302)
    user_id = request.session["user_id"]
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id, Recipe.user_id == user_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail=gettext_for(request, "Recipe not found"))
    lang = get_lang(request)
    ing_ids = [ri.ingredient_id for ri in recipe.ingredients]
    translations: dict[int, str] = {}
    if lang != "en" and ing_ids:
        rows = (
            db.query(IngredientTranslation)
            .filter(
                IngredientTranslation.ingredient_id.in_(ing_ids),
                IngredientTranslation.lang == lang,
            )
            .all()
        )
        translations = {t.ingredient_id: t.name for t in rows}
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

    # Ungrouped ingredients
    for ing in data.ungrouped_ingredients:
        db.add(
            RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ing.ingredient_id,
                amount=ing.amount,
                unit_id=ing.unit_id,
            )
        )

    # Groups + their ingredients
    for group_data in data.ingredient_groups:
        group = RecipeIngredientGroup(
            recipe_id=recipe.id,
            name=group_data.name,
            position=group_data.position,
        )
        db.add(group)
        db.flush()
        for ing in group_data.ingredients:
            db.add(
                RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=ing.ingredient_id,
                    amount=ing.amount,
                    unit_id=ing.unit_id,
                    group_id=group.id,
                )
            )

    # Steps
    for step in data.steps:
        db.add(
            Step(
                recipe_id=recipe.id,
                position=step.position,
                description=step.description,
                duration=step.duration,
            )
        )

    db.commit()
    return {"id": recipe.id}
