"""User API router.

Provides endpoints to create a user and generate a meal plan, and to list
users with their latest meal plans. Endpoints use dependency-injected DB
sessions and the recommendation service to assemble results.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json
from database.deps import get_db_read, get_db_write
from core.logger import get_logger
from core.repository import save
from core.exceptions import NotFoundError, DatabaseError, InsufficientDataError
from services.recommendation_engine import recommendation_service
from services.nutrition_calculator import nutrition_calculator
from database import models
from schemas import UserCreateRequest, UserWithMealPlanResponse, AllUsersResponse, MealDetail
from schemas.user_schema import WeeklyMealPlanResponse

logger = get_logger("api.users")
router = APIRouter(prefix="/api", tags=["users"])


@router.post("/create-user-with-plan", response_model=UserWithMealPlanResponse, status_code=201)
def create_user_with_plan(payload: UserCreateRequest, db: Session = Depends(get_db_write)):
    """Create a new user and generate both daily and weekly meal plans.

    This endpoint computes nutrition targets using the `NutritionCalculator`,
    persists the new user, generates both daily and weekly plans with
    `RecommendationEngine`, saves all plans, and returns user + plan details.

    Args:
        payload: `UserCreateRequest` with user profile info and use_csv flag.
        db: SQLAlchemy session (write) injected by dependency.

    Returns:
        `UserWithMealPlanResponse` containing user, daily plan, and weekly plan.
        
    Raises:
        InsufficientDataError: If no meals available in database or CSV.
        DatabaseError: If database operation fails.
    """
    logger.info("Creating user: %s (use_csv=%s)", payload.name, payload.use_csv)
    bmi = nutrition_calculator.calculate_bmi(payload.height, payload.weight)
    bmr = nutrition_calculator.calculate_bmr(payload.age, payload.height, payload.weight, payload.gender)
    tdee = nutrition_calculator.calculate_tdee(bmr, payload.activity_level)
    target_calories = nutrition_calculator.calculate_target_calories(tdee, payload.health_goal)
    target_macros = nutrition_calculator.calculate_macros(target_calories, payload.dietary_preference)

    user = models.User(
        name=payload.name,
        age=payload.age,
        height=payload.height,
        weight=payload.weight,
        gender=payload.gender,
        activity_level=payload.activity_level,
        dietary_preference=payload.dietary_preference,
        health_goal=payload.health_goal,
        allergies=json.dumps(payload.allergies or []),
        target_calories=target_calories,
        target_protein=target_macros['protein'],
        target_carbs=target_macros['carbs'],
        target_fat=target_macros['fat'],
    )
    user = save(db, user)

    # Source meals from CSV or database based on use_csv flag
    if payload.use_csv:
        from data.ingest_meals import parse_meals_csv
        from types import SimpleNamespace
        csv_rows = parse_meals_csv("data/fixtures/healthy_meal_plans.csv")
        all_meals = [SimpleNamespace(**{**r, "dietary_tags": r.get("dietary_tags", []), "ingredients": r.get("ingredients", [])}) for r in csv_rows]
        logger.info("Loaded %s meals from CSV", len(all_meals))
    else:
        all_meals = db.query(models.Meal).all()
        logger.info("Loaded %s meals from database", len(all_meals))
    
    if not all_meals:
        raise InsufficientDataError("No meals available. Please load meal data first.")
    
    # Generate both daily and weekly plans
    daily_plan = recommendation_service.generate_daily_meal_plan(user, all_meals)
    weekly_plan = recommendation_service.generate_weekly_meal_plan(user, all_meals)

    # Save daily plan to database
    meal_plan = models.MealPlan(
        user_id=user.id,
        plan_date=__import__('datetime').date.today(),
        breakfast_id=daily_plan['breakfast']['id'],
        lunch_id=daily_plan['lunch']['id'],
        dinner_id=daily_plan['dinner']['id'],
        snack_id=daily_plan['snack']['id'] if daily_plan.get('snack') else None,
        total_calories=daily_plan['daily_totals']['calories'],
        total_protein=daily_plan['daily_totals']['protein'],
        total_carbs=daily_plan['daily_totals']['carbs'],
        total_fat=daily_plan['daily_totals']['fat'],
    )
    save(db, meal_plan)

    # Save weekly plans to database
    from datetime import datetime
    for day_plan in weekly_plan:
        weekly_meal_plan = models.MealPlan(
            user_id=user.id,
            plan_date=datetime.fromisoformat(day_plan['date']),
            breakfast_id=day_plan['breakfast']['id'],
            lunch_id=day_plan['lunch']['id'],
            dinner_id=day_plan['dinner']['id'],
            snack_id=day_plan.get('snack', {}).get('id') if day_plan.get('snack') else None,
            total_calories=day_plan['daily_totals']['calories'],
            total_protein=day_plan['daily_totals']['protein'],
            total_carbs=day_plan['daily_totals']['carbs'],
            total_fat=day_plan['daily_totals']['fat'],
        )
        save(db, weekly_meal_plan)

    logger.info("User %s created with id=%s (daily + weekly plans)", user.name, user.id)

    response = UserWithMealPlanResponse(
        name=user.name,
        age=user.age,
        height=user.height,
        weight=user.weight,
        bmi=round(bmi, 1),
        gender=user.gender,
        activity_level=user.activity_level,
        health_goal=user.health_goal,
        dietary_preference=user.dietary_preference,
        target_calories=round(user.target_calories),
        target_macros={
            "protein": round(user.target_protein),
            "carbs": round(user.target_carbs),
            "fat": round(user.target_fat),
        },
        daily_plan=daily_plan,
        weekly_plan=weekly_plan,
        created_at=user.created_at.isoformat(),
    )
    return response


@router.post("/create-user-with-weekly-plan", response_model=WeeklyMealPlanResponse, status_code=201)
def create_user_with_weekly_plan(payload: UserCreateRequest, db: Session = Depends(get_db_write)):
    """Create a new user and generate a 7-day weekly meal plan.

    This endpoint computes nutrition targets, persists the user, generates
    a weekly meal plan with variety, saves all 7 daily plans, and returns
    user + weekly plan details.

    Args:
        payload: `UserCreateRequest` with user profile info.
        db: SQLAlchemy session (write) injected by dependency.

    Returns:
        `WeeklyMealPlanResponse` containing the user and 7-day meal plan.
        
    Raises:
        InsufficientDataError: If no meals available in database.
        DatabaseError: If database operation fails.
    """
    logger.info("Creating user with weekly plan: %s", payload.name)
    bmi = nutrition_calculator.calculate_bmi(payload.height, payload.weight)
    bmr = nutrition_calculator.calculate_bmr(payload.age, payload.height, payload.weight, payload.gender)
    tdee = nutrition_calculator.calculate_tdee(bmr, payload.activity_level)
    target_calories = nutrition_calculator.calculate_target_calories(tdee, payload.health_goal)
    target_macros = nutrition_calculator.calculate_macros(target_calories, payload.dietary_preference)

    user = models.User(
        name=payload.name,
        age=payload.age,
        height=payload.height,
        weight=payload.weight,
        gender=payload.gender,
        activity_level=payload.activity_level,
        dietary_preference=payload.dietary_preference,
        health_goal=payload.health_goal,
        allergies=json.dumps(payload.allergies or []),
        target_calories=target_calories,
        target_protein=target_macros['protein'],
        target_carbs=target_macros['carbs'],
        target_fat=target_macros['fat'],
    )
    user = save(db, user)

    all_meals = db.query(models.Meal).all()
    if not all_meals:
        raise InsufficientDataError("No meals available in database. Please load meal data first.")
    
    weekly_plan = recommendation_service.generate_weekly_meal_plan(user, all_meals)

    # Save all 7 daily plans to database
    from datetime import datetime
    for day_plan in weekly_plan:
        meal_plan = models.MealPlan(
            user_id=user.id,
            plan_date=datetime.fromisoformat(day_plan['date']),
            breakfast_id=day_plan['breakfast']['id'],
            lunch_id=day_plan['lunch']['id'],
            dinner_id=day_plan['dinner']['id'],
            snack_id=day_plan.get('snack', {}).get('id') if day_plan.get('snack') else None,
            total_calories=day_plan['daily_totals']['calories'],
            total_protein=day_plan['daily_totals']['protein'],
            total_carbs=day_plan['daily_totals']['carbs'],
            total_fat=day_plan['daily_totals']['fat'],
        )
        save(db, meal_plan)

    logger.info("User %s created with weekly plan (id=%s)", user.name, user.id)

    response = WeeklyMealPlanResponse(
        name=user.name,
        age=user.age,
        height=user.height,
        weight=user.weight,
        bmi=round(bmi, 1),
        gender=user.gender,
        activity_level=user.activity_level,
        health_goal=user.health_goal,
        dietary_preference=user.dietary_preference,
        target_calories=round(user.target_calories),
        target_macros={
            "protein": round(user.target_protein),
            "carbs": round(user.target_carbs),
            "fat": round(user.target_fat),
        },
        weekly_plan=weekly_plan,
        created_at=user.created_at.isoformat(),
    )
    return response


@router.get("/users-with-plans", response_model=AllUsersResponse)
def get_users_with_plans(limit: int = 50, skip: int = 0, db: Session = Depends(get_db_read)):
    """Return a paginated list of users together with their latest meal plan.

    Args:
        limit (int): Maximum number of users to return.
        skip (int): Number of users to skip (pagination).
        db: Read-only SQLAlchemy session injected by dependency.

    Returns:
        `AllUsersResponse` containing total_users and list of user objects.
    """
    users = db.query(models.User).offset(skip).limit(limit).all()
    result = []
    for u in users:
        latest_plan = db.query(models.MealPlan).filter(models.MealPlan.user_id == u.id).order_by(models.MealPlan.plan_date.desc()).first()
        if latest_plan:
            def meal_to_detail(meal_id):
                """Convert a meal ID to MealDetail schema object.
                
                Args:
                    meal_id: Database ID of the meal.
                    
                Returns:
                    MealDetail object or None if meal not found.
                """
                m = db.query(models.Meal).get(meal_id)
                if not m:
                    return None
                return MealDetail(
                    id=m.id,
                    name=m.name,
                    meal_type=m.meal_type,
                    calories=m.calories,
                    protein=m.protein,
                    carbs=m.carbs,
                    fat=m.fat,
                    ingredients=json.loads(m.ingredients),
                )

            plan_obj = {
                "date": latest_plan.plan_date.isoformat(),
                "breakfast": meal_to_detail(latest_plan.breakfast_id),
                "lunch": meal_to_detail(latest_plan.lunch_id),
                "dinner": meal_to_detail(latest_plan.dinner_id),
                "snack": meal_to_detail(latest_plan.snack_id) if latest_plan.snack_id else None,
                "daily_totals": {
                    "calories": latest_plan.total_calories,
                    "protein": latest_plan.total_protein,
                    "carbs": latest_plan.total_carbs,
                    "fat": latest_plan.total_fat,
                }
            }
        else:
            plan_obj = None
        result.append({
            "user_id": u.id,
            "name": u.name,
            "age": u.age,
            "height": u.height,
            "weight": u.weight,
            "bmi": round(nutrition_calculator.calculate_bmi(u.height, u.weight),1),
            "health_goal": u.health_goal,
            "dietary_preference": u.dietary_preference,
            "target_calories": round(u.target_calories),
            "target_macros": {"protein": round(u.target_protein), "carbs": round(u.target_carbs), "fat": round(u.target_fat)},
            "meal_plan": plan_obj,
            "created_at": u.created_at.isoformat(),
        })

    return AllUsersResponse(total_users=len(result), users=result)
