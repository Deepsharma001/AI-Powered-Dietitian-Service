"""Schemas for meal-related responses and plan structures."""

from pydantic import BaseModel
from typing import List, Optional


class MealDetail(BaseModel):
    """Representation of a meal in responses."""

    id: int
    name: str
    meal_type: str
    calories: float
    protein: float
    carbs: float
    fat: float
    ingredients: List[str]


class SimilarMeal(BaseModel):
    """Similar meal with an attached similarity score."""

    id: int
    name: str
    meal_type: str
    calories: float
    protein: float
    carbs: float
    fat: float
    dietary_tags: List[str] = []
    ingredients: List[str]
    score: float


class DailyMealPlan(BaseModel):
    """Daily meal plan payload returned for a user."""

    date: str
    breakfast: MealDetail
    lunch: MealDetail
    dinner: MealDetail
    snack: Optional[MealDetail] = None
    daily_totals: dict