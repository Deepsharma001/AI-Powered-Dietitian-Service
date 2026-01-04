"""Schemas for feedback submission and response."""

from pydantic import BaseModel, Field
from typing import Optional


class FeedbackCreateRequest(BaseModel):
    """Payload for submitting a feedback rating for a meal."""

    user_id: int = Field(..., examples=[1], description="ID of the user providing feedback")
    plan_id: Optional[int] = Field(None, examples=[5], description="ID of the meal plan (optional)")
    meal_id: int = Field(..., examples=[10], description="ID of the meal being rated")
    rating: int = Field(..., ge=1, le=5, examples=[4], description="Rating from 1 (poor) to 5 (excellent)")


class FeedbackResponse(BaseModel):
    """Stored feedback record returned after persisting."""

    id: int
    user_id: int
    plan_id: Optional[int]
    meal_id: int
    rating: int
    created_at: str