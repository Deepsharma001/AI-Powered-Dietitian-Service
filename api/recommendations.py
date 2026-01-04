"""Recommendation-related endpoints.

Includes endpoints for submitting feedback and for retrieving content-based
similarities for meals. Feedback is persisted for later training of CF models.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.deps import get_db_write
from database import models
from schemas.feedback_schema import FeedbackCreateRequest, FeedbackResponse
from schemas.meal_schema import SimilarMeal
from services.content_recommender import content_recommender
from database.deps import get_db_read
from core.logger import get_logger
from core.repository import save
from core.exceptions import NotFoundError
from datetime import datetime
from typing import List
import json

logger = get_logger("api.recommendations")
router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.post("/{plan_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(plan_id: int, payload: FeedbackCreateRequest, db: Session = Depends(get_db_write)):
    """Record a user's feedback for a meal within a meal plan.

    Validates that the user and meal exist, persists a Feedback record, and
    returns the stored feedback details.
    
    Raises:
        NotFoundError: If user or meal not found in database.
    """
    # basic validations
    user = db.get(models.User, payload.user_id)
    if not user:
        raise NotFoundError("User", payload.user_id)
    meal = db.get(models.Meal, payload.meal_id)
    if not meal:
        raise NotFoundError("Meal", payload.meal_id)

    fb = models.Feedback(
        user_id=payload.user_id,
        plan_id=plan_id,
        meal_id=payload.meal_id,
        rating=payload.rating,
        created_at=datetime.utcnow()
    )
    fb = save(db, fb)
    logger.info("Feedback recorded: user=%s meal=%s rating=%s", payload.user_id, payload.meal_id, payload.rating)
    return FeedbackResponse(id=fb.id, user_id=fb.user_id, plan_id=fb.plan_id, meal_id=fb.meal_id, rating=fb.rating, created_at=fb.created_at.isoformat())


@router.get("/meal/{meal_id}/similar", response_model=List[SimilarMeal])
def get_similar_meals(meal_id: int, top_k: int = 5, db: Session = Depends(get_db_read)):
    """Return the top-k meals most similar to the given meal id.

    Uses the content-based recommender to rank meals by cosine similarity and
    returns serialized `SimilarMeal` objects including the similarity score.
    
    Raises:
        NotFoundError: If meal not found in database.
    """
    # Verify meal exists
    meal = db.get(models.Meal, meal_id)
    if not meal:
        raise NotFoundError("Meal", meal_id)
    
    ranked = content_recommender.recommend_similar(db, meal_id, top_k)
    results = []
    for meal_id, score in ranked:
        m = db.get(models.Meal, meal_id)
        tags = []
        try:
            tags = json.loads(m.dietary_tags) if m.dietary_tags else []
        except Exception:
            try:
                tags = eval(m.dietary_tags)
            except Exception:
                tags = []
        results.append(SimilarMeal(
            id=m.id,
            name=m.name,
            meal_type=m.meal_type,
            calories=m.calories,
            protein=m.protein,
            carbs=m.carbs,
            fat=m.fat,
            dietary_tags=tags,
            ingredients=json.loads(m.ingredients) if m.ingredients else [],
            score=score
        ))
    return results
