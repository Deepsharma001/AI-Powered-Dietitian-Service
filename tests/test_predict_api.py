"""Tests for the predict endpoint returning recommended meals."""
from services.diet_trainer import load_model, train_from_csv
from database.database import ReadSessionLocal
from schemas.diet_schema import PredictRequest
from api.train import predict


def test_predict_returns_recommended_meals():
    # Ensure model exists
    model = load_model()
    if model is None:
        train_from_csv('/home/deepak/Downloads/archive/diet_recommendations_dataset.csv', test_size=0.3)

    profile = {
        "Age": 50,
        "Gender": "Male",
        "Weight_kg": 80,
        "Height_cm": 170,
        "Physical_Activity_Level": "Moderate",
        "Daily_Caloric_Intake": 2200,
        "Dietary_Restrictions": None,
        "Allergies": None,
        "Preferred_Cuisine": "Indian",
        "Weekly_Exercise_Hours": 3.0,
    }

    db = ReadSessionLocal()
    try:
        req = PredictRequest(profile=profile)
        res = predict(req, db)
        assert hasattr(res, 'diet_recommendation') and hasattr(res, 'recommended_meals')
        assert isinstance(res.recommended_meals, list)
        # Ensure fallback scoring or tag matching returns at least one meal
        assert len(res.recommended_meals) > 0, "No recommended meals returned; fallback failed"
    finally:
        db.close()


def test_predict_respects_dietary_preference():
    db = ReadSessionLocal()
    try:
        vegan_profile = {
            "Age": 35,
            "Gender": "Female",
            "Weight_kg": 65,
            "Height_cm": 165,
            "Physical_Activity_Level": "Light",
            "Dietary_Preference": "Vegan",
        }
        req = PredictRequest(profile=vegan_profile)
        res = predict(req, db)
        assert isinstance(res.recommended_meals, list)
        assert len(res.recommended_meals) > 0
        # all returned meals should be verified for vegan preference
        for m in res.recommended_meals:
            assert 'verified' in m
            assert m['verified'] is True, f"Meal {m['id']} is not verified as vegan"
            from database import models
            meal_obj = db.get(models.Meal, m['id'])
            import json as _json
            tags = _json.loads(meal_obj.dietary_tags) if meal_obj.dietary_tags else []
            assert any('vegan' in str(t).lower() for t in tags), f"Meal {m['id']} tags do not indicate vegan: {tags}"
    finally:
        db.close()
