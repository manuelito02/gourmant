import re

from pydantic import BaseModel, field_validator

from app.models.ingredient import DietClassification

# Matches filenames produced by the upload endpoint: 32 lowercase hex chars + .jpg
_FILENAME_RE = re.compile(r"^[0-9a-f]{32}\.jpg$")


def _validate_filename(v: str) -> str:
    if not _FILENAME_RE.match(v):
        raise ValueError("invalid image filename")
    return v


class IngredientCreate(BaseModel):
    name: str
    type_id: int
    classification: DietClassification = DietClassification.VEGAN


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
    image_filenames: list[str] = []

    @field_validator("image_filenames", mode="before")
    @classmethod
    def validate_image_filenames(cls, v: list) -> list:
        for fn in v:
            _validate_filename(fn)
        return v


class RecipeCreate(BaseModel):
    title: str
    description: str | None = None
    type_id: int
    servings: int | None = None
    image_filename: str | None = None
    ungrouped_ingredients: list[RecipeIngredientIn] = []
    ingredient_groups: list[IngredientGroupIn] = []
    steps: list[StepIn] = []

    @field_validator("image_filename")
    @classmethod
    def validate_image_filename(cls, v: str | None) -> str | None:
        if v is not None:
            _validate_filename(v)
        return v
