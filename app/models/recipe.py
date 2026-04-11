from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.ingredient import AmountUnit, Ingredient


class RecipeType(Base):
    __tablename__ = "recipe_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    recipes: Mapped[list["Recipe"]] = relationship(back_populates="type")


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    type_id: Mapped[int] = mapped_column(ForeignKey("recipe_types.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    type: Mapped["RecipeType"] = relationship(back_populates="recipes")
    ingredient_groups: Mapped[list["RecipeIngredientGroup"]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="RecipeIngredientGroup.position",
    )
    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )
    steps: Mapped[list["Step"]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="Step.position",
    )


class RecipeIngredientGroup(Base):
    __tablename__ = "recipe_ingredient_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(nullable=False)

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredient_groups")
    ingredients: Mapped[list["RecipeIngredient"]] = relationship(back_populates="group")


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    unit_id: Mapped[int] = mapped_column(ForeignKey("amount_units.id"), nullable=False)
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipe_ingredient_groups.id"), nullable=True
    )

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")
    ingredient: Mapped[Ingredient] = relationship()
    unit: Mapped[AmountUnit] = relationship()
    group: Mapped["RecipeIngredientGroup | None"] = relationship(back_populates="ingredients")


class Step(Base):
    __tablename__ = "steps"
    __table_args__ = (UniqueConstraint("recipe_id", "position", name="uq_step_recipe_position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False)
    position: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    duration: Mapped[int | None] = mapped_column(nullable=True)  # minutes

    recipe: Mapped["Recipe"] = relationship(back_populates="steps")
