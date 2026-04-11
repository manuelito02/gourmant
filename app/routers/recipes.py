from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ingredient import Ingredient, IngredientType
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
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


def _require_user(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
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
    return templates.TemplateResponse(request, "dashboard.html", {"recipes": recipes})


@router.get("/recipes/new", response_class=HTMLResponse)
def new_recipe_form(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=302)
    recipe_types = db.query(RecipeType).order_by(RecipeType.name).all()
    amount_units = db.query(AmountUnit).all()
    ingredient_types = db.query(IngredientType).order_by(IngredientType.name).all()
    return templates.TemplateResponse(
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


# ── Ingredient API ────────────────────────────────────────────────────────────


@router.get("/api/ingredients")
def search_ingredients(q: str = "", db: Session = Depends(get_db)):
    results = (
        db.query(Ingredient)
        .filter(Ingredient.name.ilike(f"%{q}%"))
        .order_by(Ingredient.name)
        .limit(20)
        .all()
    )
    return [{"id": i.id, "name": i.name} for i in results]


@router.post("/api/ingredients", status_code=201)
def create_ingredient(data: IngredientCreate, request: Request, db: Session = Depends(get_db)):
    _require_user(request)
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    if db.query(Ingredient).filter(Ingredient.name.ilike(name)).first():
        raise HTTPException(status_code=400, detail="Ingredient already exists")
    ing = Ingredient(name=name, type_id=data.type_id)
    db.add(ing)
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
