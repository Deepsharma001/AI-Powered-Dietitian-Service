"""Schemas for user-related requests and responses."""

from pydantic import BaseModel, Field
from typing import List, Optional


class UserCreateRequest(BaseModel):
    """Request payload for creating a user profile."""

    name: str = Field(..., min_length=1, examples=["John Doe"], description="User's full name")
    age: int = Field(..., ge=18, le=100, examples=[30], description="Age in years (18-100)")
    height: float = Field(..., ge=100, le=250, examples=[175.0], description="Height in centimeters (100-250)")
    weight: float = Field(..., ge=30, le=300, examples=[75.0], description="Weight in kilograms (30-300)")
    gender: str = Field(..., examples=["male"], description="Gender (male/female)")
    activity_level: str = Field(..., examples=["moderately_active"], description="Activity level: sedentary, lightly_active, moderately_active, very_active, extremely_active")
    dietary_preference: str = Field(..., examples=["balanced"], description="Dietary preference: balanced, keto, vegetarian, vegan, paleo, mediterranean, high-protein")
    health_goal: str = Field(..., examples=["maintain"], description="Health goal: weight_loss, muscle_gain, maintain")
    allergies: Optional[List[str]] = Field(default=[], examples=[["peanuts", "shellfish"]], description="List of food allergies")
    use_csv: Optional[bool] = Field(default=False, examples=[False], description="If true, source meals from CSV fixtures instead of database")


class UserWithMealPlanResponse(BaseModel):
    """Response returned after creating a user with a generated meal plan."""

    name: str
    age: int
    height: float
    weight: float
    bmi: float
    gender: str
    activity_level: str
    health_goal: str
    dietary_preference: str
    target_calories: float
    target_macros: dict
    daily_plan: dict
    weekly_plan: List[dict]
    created_at: str


class WeeklyMealPlanResponse(BaseModel):
    """Response containing a 7-day weekly meal plan."""

    name: str
    age: int
    height: float
    weight: float
    bmi: float
    gender: str
    activity_level: str
    health_goal: str
    dietary_preference: str
    target_calories: float
    target_macros: dict
    weekly_plan: List[dict] = Field(..., description="List of 7 daily meal plans")
    created_at: str