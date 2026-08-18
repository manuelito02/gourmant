import enum

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DietClassification(enum.StrEnum):
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    PESCATARIAN = "pescatarian"
    MEAT = "meat"


DIET_ORDER = list(DietClassification)


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
    type_id: Mapped[int] = mapped_column(ForeignKey("ingredient_types.id"), nullable=False)
    classification: Mapped[DietClassification] = mapped_column(
        Enum(
            DietClassification,
            name="dietclassification",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        server_default=DietClassification.VEGAN.value,
    )

    type: Mapped["IngredientType"] = relationship(back_populates="ingredients")
    translations: Mapped[list["IngredientTranslation"]] = relationship(
        back_populates="ingredient", cascade="all, delete-orphan"
    )


class IngredientTranslation(Base):
    __tablename__ = "ingredient_translations"
    __table_args__ = (UniqueConstraint("ingredient_id", "lang"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False
    )
    lang: Mapped[str] = mapped_column(String(5), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    ingredient: Mapped["Ingredient"] = relationship(back_populates="translations")
