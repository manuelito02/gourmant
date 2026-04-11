from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class IngredientType(Base):
    __tablename__ = "ingredient_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    ingredients: Mapped[list["Ingredient"]] = relationship(back_populates="type")


class AmountUnit(Base):
    __tablename__ = "amount_units"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    abbreviation: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    type_id: Mapped[int] = mapped_column(nullable=False)

    type: Mapped["IngredientType"] = relationship(back_populates="ingredients")
