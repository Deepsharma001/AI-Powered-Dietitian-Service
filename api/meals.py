"""Meals API router.

Small router that exposes meal listings used by the frontend and internal
components. Meals are returned in `MealDetail` schema format.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import json
from database.deps import get_db_read
from core.logger import get_logger
from database import models
from schemas import MealDetail

logger = get_logger("api.meals")
router = APIRouter(prefix="/api", tags=["meals"])


@router.get("/meals", response_model=List[MealDetail])
def list_meals(db: Session = Depends(get_db_read)):
    """Return all meals as a list of `MealDetail` objects.

    Args:
        db: Read-only SQLAlchemy session injected by dependency.

    Returns:
        List of meal objects in `MealDetail` Pydantic format.
    """
    meals = db.query(models.Meal).all()
    out = []
    for m in meals:
        out.append(MealDetail(
            id=m.id,
            name=m.name,
            meal_type=m.meal_type,
            calories=m.calories,
            protein=m.protein,
            carbs=m.carbs,
            fat=m.fat,
            ingredients=json.loads(m.ingredients),
        ))
    return out
