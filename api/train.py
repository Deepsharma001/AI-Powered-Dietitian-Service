"""Endpoints for training and predicting diet recommendations."""
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Optional, Dict, Any
from pydantic import BaseModel
import json
from services.diet_trainer import train_from_csv, predict_from_profile, load_model
from services.recommendation_engine import recommendation_service
from database.deps import get_db_read
from database import models
from core.logger import get_logger
from core.exceptions import NotFoundError, ModelNotTrainedError, ValidationError, InsufficientDataError

logger = get_logger("api.train")
router = APIRouter(prefix="/api/diet", tags=["diet"])

DEFAULT_CSV = "/home/deepak/Downloads/archive/diet_recommendations_dataset.csv"


class TrainRequest(BaseModel):
    """Request schema for training the diet model.
    
    Attributes:
        csv_path: Optional path to CSV file. Uses default dataset if None.
    """
    csv_path: Optional[str] = None


class TrainResponse(BaseModel):
    """Response schema containing training results.
    
    Attributes:
        model_path: Path where the trained model was saved.
        accuracy: Model accuracy score on test set.
        classes: List of predicted class labels.
    """
    model_path: str
    accuracy: float
    classes: list


class PredictRequest(BaseModel):
    """Request schema for diet prediction endpoint.
    
    Attributes:
        user_id: Optional user ID to load profile from database.
        profile: Optional inline profile dictionary with user attributes.
        use_csv: If True, source meals from CSV fixtures instead of DB.
        preference: Explicit dietary preference (e.g., 'veg', 'vegan', 'keto').
    """
    user_id: Optional[int] = None
    profile: Optional[Dict[str, Any]] = None
    use_csv: Optional[bool] = False  # if true, source meals from CSV fixtures instead of DB
    preference: Optional[str] = None  # explicit dietary preference (veg, vegan, keto, etc.)


class PredictResponse(BaseModel):
    """Response schema containing prediction results and recommendations.
    
    Attributes:
        user_id: User ID if prediction was for an existing user.
        name: User name.
        age: User age.
        height: User height in cm.
        weight: User weight in kg.
        bmi: Calculated BMI.
        gender: User gender.
        activity_level: Physical activity level.
        health_goal: User's health goal.
        dietary_preference: Dietary preference.
        target_calories: Calculated target calories.
        target_macros: Target macronutrient goals (protein, carbs, fat).
        diet_recommendation: Predicted diet category label.
        confidence: Confidence score for the prediction.
        probabilities: Dictionary mapping each class to its probability.
        recommended_meals: List of recommended meal objects.
        daily_plan: Generated daily meal plan with breakfast, lunch, dinner.
    """
    user_id: Optional[int] = None
    name: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    bmi: Optional[float] = None
    gender: Optional[str] = None
    activity_level: Optional[str] = None
    health_goal: Optional[str] = None
    dietary_preference: str
    target_calories: Optional[float] = None
    target_macros: Optional[dict] = None
    diet_recommendation: str
    confidence: float
    probabilities: Dict[str, float]
    recommended_meals: Optional[list] = None
    daily_plan: Optional[dict] = None


@router.post("/train", response_model=TrainResponse)
def train(request: TrainRequest = Body(...)):
    """Train the diet recommendation model from CSV and return metrics."""
    path = request.csv_path or DEFAULT_CSV
    try:
        res = train_from_csv(path)
        return TrainResponse(model_path=res["model_path"], accuracy=res["accuracy"], classes=res["classes"])
    except Exception as exc:
        logger.exception("Training failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest = Body(...), db=Depends(get_db_read)):
    """Predict diet recommendation from a user id or an inline profile.
    
    Raises:
        ValidationError: If neither user_id nor profile provided.
        NotFoundError: If user_id provided but user not found.
        ModelNotTrainedError: If ML model not trained yet.
        InsufficientDataError: If no meals available.
    """
    if request.user_id is None and request.profile is None:
        raise ValidationError("Either user_id or profile must be provided")

    profile = None
    if request.user_id is not None:
        user = db.get(models.User, request.user_id)
        if not user:
            raise NotFoundError("User", request.user_id)
        # map user fields to expected profile keys
        profile = {
            "Age": user.age,
            "Gender": user.gender,
            "Weight_kg": user.weight,
            "Height_cm": user.height,
            "Physical_Activity_Level": user.activity_level,
            "Daily_Caloric_Intake": None,
            "Dietary_Restrictions": None,
            "Allergies": user.allergies,
            "Preferred_Cuisine": None,
            "Weekly_Exercise_Hours": None,
        }
    else:
        profile = request.profile

    try:
        out = predict_from_profile(profile)

        # find meals that match predicted diet label using dietary_tags
        diet_label = out.get("diet_recommendation", "").lower()
        meals = []
        try:
            # If requested, use CSV fixtures as source of meals
            if request.use_csv:
                from data.ingest_meals import parse_meals_csv
                from types import SimpleNamespace
                csv_rows = parse_meals_csv("data/fixtures/healthy_meal_plans.csv")
                all_meals = [SimpleNamespace(**{**r, "dietary_tags": r.get("dietary_tags", []), "ingredients": r.get("ingredients", [])}) for r in csv_rows]
            else:
                all_meals = db.query(models.Meal).all()

            # map common model labels to dietary tags used in meals
            LABEL_TO_TAG = {
                'balanced': 'is_healthy',
                'low_carb': 'keto',
                'low-carb': 'keto',
                'low_sodium': 'low_sodium',
                'low-sodium': 'low_sodium',
                'high_protein': 'high-protein',
                'gluten_free': 'gluten_free',
                'vegetarian': 'vegetarian',
                'vegan': 'vegan',
                'paleo': 'paleo',
                'mediterranean': 'mediterranean'
            }

            target_tag = LABEL_TO_TAG.get(diet_label, diet_label)

            # Find by tag
            matched_by_tag = []
            for m in all_meals:
                tags = []
                try:
                    tags = json.loads(m.dietary_tags) if isinstance(m.dietary_tags, str) else (m.dietary_tags or [])
                except Exception:
                    try:
                        tags = eval(m.dietary_tags)
                    except Exception:
                        tags = []
                if any(target_tag == str(t).strip().lower() for t in tags):
                    matched_by_tag.append(m)
            meals = matched_by_tag
            # debug info to help trace CSV matching in test environments
            logger.debug("CSV debug: parsed_rows=%s, sample_tags=%s", len(all_meals), [ (getattr(m,'name',None), m.dietary_tags) for m in all_meals[:5] ])
            logger.debug("CSV debug: matched_by_tag_count=%s target_tag=%s", len(matched_by_tag), target_tag)
            logger.debug("Matched by tag: %s", len(matched_by_tag))

            # fallback 1: use recommendation_service filter to find candidates using target_tag
            if not meals and target_tag:
                meals = recommendation_service.filter_meals_by_preference(all_meals, target_tag)
                logger.debug("After filter_meals_by_preference: %s", len(meals))

            # fallback 2: score all meals against a generic macro target derived from the diet label
            if not meals and diet_label:
                try:
                    # use a default calorie baseline and convert to per-meal target
                    default_cals = 2000
                    macros = recommendation_service.calculate_macros(default_cals, diet_label)
                    per_meal_cals = default_cals / 3
                    # score_meal expects attributes on meal, adapt when rows are dict-like
                    scored = [(recommendation_service.score_meal(m, per_meal_cals, macros), m) for m in all_meals]
                    scored.sort(key=lambda x: x[0], reverse=True)
                    meals = [m for _, m in scored[:10]]
                    logger.debug("After scoring fallback: %s", len(meals))
                except Exception:
                    meals = []
        except Exception as exc:
            logger.exception("Error while sourcing candidate meals: %s", exc)
            meals = []

# decide desired dietary preference from request.preference, profile, or predicted label
        desired_pref = None
        explicit_pref = False
        try:
            # top-level request preference overrides profile
            if request.preference:
                desired_pref = str(request.preference).strip().lower()
                explicit_pref = True
            elif profile and isinstance(profile, dict):
                # accept multiple possible keys
                pref = profile.get('Dietary_Preference') or profile.get('dietary_preference') or profile.get('Dietary_Restrictions')
                if isinstance(pref, str):
                    desired_pref = pref.strip().lower()
                    explicit_pref = True
            if desired_pref is None and diet_label:
                desired_pref = diet_label

            # normalize common shorthand values
            PREF_MAP = {
                'veg': 'vegetarian',
                'vegetarian': 'vegetarian',
                'vegan': 'vegan',
                'keto': 'keto',
                'low_carb': 'keto',
                'low-carb': 'keto',
                'gluten_free': 'gluten_free',
                'gluten-free': 'gluten_free',
                'paleo': 'paleo',
                'mediterranean': 'mediterranean',
                'balanced': 'is_healthy',
            }
            if desired_pref in PREF_MAP:
                desired_tag = PREF_MAP[desired_pref]
            else:
                desired_tag = desired_pref
        except Exception:
            desired_pref = None
            desired_tag = None

        # If the request explicitly included a dietary preference, enforce verification by filtering
        if explicit_pref and desired_tag:
            pref_filtered = []
            for m in meals:
                try:
                    tags = json.loads(m.dietary_tags) if m.dietary_tags else []
                except Exception:
                    try:
                        tags = eval(m.dietary_tags)
                    except Exception:
                        tags = []
                if any(str(t).strip().lower() == str(desired_tag).strip().lower() or str(desired_tag) in str(t).strip().lower() for t in tags):
                    pref_filtered.append(m)
            # If no matches in the current candidate set, try global filter across all meals
            if not pref_filtered and desired_tag:
                pref_filtered = recommendation_service.filter_meals_by_preference(all_meals, desired_tag)
            meals = pref_filtered

        # build meal details (limit top 10) and mark verification status
        recommended_meals = []
        for m in meals[:10]:
            try:
                # robustly parse tags and ingredients whether data comes from DB or CSV rows
                tags = []
                if hasattr(m, 'dietary_tags'):
                    if isinstance(m.dietary_tags, (list, tuple)):
                        tags = [str(t).lower() for t in m.dietary_tags]
                    else:
                        try:
                            tags = [str(t).lower() for t in json.loads(m.dietary_tags)]
                        except Exception:
                            try:
                                tags = [str(t).lower() for t in eval(m.dietary_tags)]
                            except Exception:
                                tags = []

                if hasattr(m, 'ingredients'):
                    if isinstance(m.ingredients, (list, tuple)):
                        ingredients = m.ingredients
                    else:
                        try:
                            ingredients = json.loads(m.ingredients)
                        except Exception:
                            try:
                                ingredients = eval(m.ingredients)
                            except Exception:
                                ingredients = []
                else:
                    ingredients = []

                is_verified = False
                if desired_tag:
                    is_verified = any(desired_tag == t or desired_tag in t for t in tags)

                recommended_meals.append({
                    "id": getattr(m, 'id', None),
                    "name": getattr(m, 'name', None),
                    "meal_type": getattr(m, 'meal_type', None),
                    "calories": getattr(m, 'calories', None),
                    "protein": getattr(m, 'protein', None),
                    "carbs": getattr(m, 'carbs', None),
                    "fat": getattr(m, 'fat', None),
                    "ingredients": ingredients,
                    "verified": is_verified,
                })
            except Exception:
                # skip any problematic rows but continue
                continue

        # optionally generate a daily plan tailored to user/profile
        daily_plan = None
        try:
            # assemble a temporary profile with targets if possible
            from types import SimpleNamespace
            user_obj = None
            if request.user_id is not None:
                user_obj = db.get(models.User, request.user_id)
            else:
                # derive targets from inline profile
                if profile:
                    # compute TDEE/macros using nutrition calculator
                    from services.nutrition_calculator import nutrition_calculator
                    bmr = nutrition_calculator.calculate_bmr(profile.get('Age', 30), profile.get('Height_cm', 170), profile.get('Weight_kg', 70), profile.get('Gender', 'male'))
                    tdee = nutrition_calculator.calculate_tdee(bmr, profile.get('Physical_Activity_Level', 'moderately_active'))
                    target_cals = nutrition_calculator.calculate_target_calories(tdee, 'maintain')
                    macros = nutrition_calculator.calculate_macros(target_cals, diet_label)
                    user_obj = SimpleNamespace(target_calories=target_cals, target_protein=macros['protein'], target_carbs=macros['carbs'], target_fat=macros['fat'], dietary_preference=diet_label, allergies=json.dumps(profile.get('Allergies') or []))
            if user_obj is not None:
                # Use same meal source (CSV or DB) as recommended_meals
                plan = recommendation_service.generate_daily_meal_plan(user_obj, all_meals)
                daily_plan = plan
        except Exception as exc:
            logger.exception("Failed to generate daily_plan: %s", exc)
            daily_plan = None

        # Build comprehensive response with user profile info
        from services.nutrition_calculator import nutrition_calculator
        
        # Calculate user profile details
        user_data = {}
        if request.user_id is not None:
            user = db.get(models.User, request.user_id)
            user_data = {
                'user_id': user.id,
                'name': user.name,
                'age': user.age,
                'height': user.height,
                'weight': user.weight,
                'bmi': round(nutrition_calculator.calculate_bmi(user.height, user.weight), 1),
                'gender': user.gender,
                'activity_level': user.activity_level,
                'health_goal': user.health_goal,
                'dietary_preference': user.dietary_preference,
                'target_calories': round(user.target_calories),
                'target_macros': {
                    'protein': round(user.target_protein),
                    'carbs': round(user.target_carbs),
                    'fat': round(user.target_fat)
                }
            }
        else:
            # For inline profiles, calculate targets
            age = profile.get('Age', 30)
            height = profile.get('Height_cm', 170)
            weight = profile.get('Weight_kg', 70)
            gender = profile.get('Gender', 'male')
            activity = profile.get('Physical_Activity_Level', 'moderately_active')
            
            bmi = nutrition_calculator.calculate_bmi(height, weight)
            bmr = nutrition_calculator.calculate_bmr(age, height, weight, gender)
            tdee = nutrition_calculator.calculate_tdee(bmr, activity)
            target_cals = nutrition_calculator.calculate_target_calories(tdee, 'maintain')
            macros = nutrition_calculator.calculate_macros(target_cals, diet_label)
            
            user_data = {
                'user_id': None,
                'name': profile.get('name', 'Guest User'),
                'age': age,
                'height': height,
                'weight': weight,
                'bmi': round(bmi, 1),
                'gender': gender,
                'activity_level': activity,
                'health_goal': profile.get('health_goal', 'maintain'),
                'dietary_preference': diet_label,
                'target_calories': round(target_cals),
                'target_macros': {
                    'protein': round(macros['protein']),
                    'carbs': round(macros['carbs']),
                    'fat': round(macros['fat'])
                }
            }

        out['recommended_meals'] = recommended_meals
        out['daily_plan'] = daily_plan
        out.update(user_data)
        return PredictResponse(**out)
    except ModelNotTrainedError:
        raise
    except NotFoundError:
        raise
    except ValidationError:
        raise
    except InsufficientDataError:
        raise
    except Exception as exc:
        logger.exception("Prediction failed")
        raise