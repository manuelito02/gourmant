from pydantic import BaseModel


class IngredientCreate(BaseModel):
    name: str
    type_id: int


class RecipeIngredientIn(BaseModel):
    ingredient_id: int
    amount: float
    unit_id: int


class IngredientGroupIn(BaseModel):
    name: str
    position: int
    ingredients: list[RecipeIngredientIn] = []


class StepIn(BaseModel):
    position: int
    description: str
    duration: int | None = None


class RecipeCreate(BaseModel):
    title: str
    description: str | None = None
    type_id: int
    ungrouped_ingredients: list[RecipeIngredientIn] = []
    ingredient_groups: list[IngredientGroupIn] = []
    steps: list[StepIn] = []
