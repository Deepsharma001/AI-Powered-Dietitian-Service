"""Schemas for diet training and prediction endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class TrainRequest(BaseModel):
    csv_path: Optional[str] = Field(None, examples=["/path/to/diet_dataset.csv"], description="Path to training CSV file (optional, uses default if not provided)")


class TrainResponse(BaseModel):
    model_path: str
    accuracy: float
    classes: list


class PredictRequest(BaseModel):
    user_id: Optional[int] = Field(None, examples=[1], description="User ID to load profile from database")
    profile: Optional[Dict[str, Any]] = Field(
        None, 
        examples=[{
            "Age": 30,
            "Gender": "Male",
            "Weight_kg": 75,
            "Height_cm": 175,
            "Physical_Activity_Level": "Moderate",
            "Dietary_Preference": "balanced"
        }],
        description="Inline user profile dictionary (alternative to user_id)"
    )
    use_csv: Optional[bool] = Field(False, examples=[False], description="If true, source meals from CSV fixtures instead of database")
    preference: Optional[str] = Field(None, examples=["vegetarian"], description="Explicit dietary preference: veg, vegetarian, vegan, keto, gluten_free, etc.")
    weekly: Optional[bool] = Field(False, examples=[False], description="If true, generate 7-day weekly plan instead of single day plan")


from typing import List, Optional
from .meal_schema import MealDetail, DailyMealPlan


class PredictResponse(BaseModel):
    diet_recommendation: str
    confidence: float
    probabilities: Dict[str, float]
    recommended_meals: Optional[List[MealDetail]] = None
    daily_plan: Optional[DailyMealPlan] = None
