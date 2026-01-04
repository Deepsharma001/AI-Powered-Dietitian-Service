"""Tests for CSV-based predict behavior."""
from database.database import ReadSessionLocal
from schemas.diet_schema import PredictRequest
from api.train import predict


def test_predict_using_csv_source():
    db = ReadSessionLocal()
    try:
        profile = {
            "Age": 45,
            "Gender": "Male",
            "Weight_kg": 85,
            "Height_cm": 175,
            "Physical_Activity_Level": "Moderate",
            "Dietary_Preference": None,
        }
        req = PredictRequest(profile=profile, use_csv=True)
        res = predict(req, db)
        assert hasattr(res, 'recommended_meals')
        assert isinstance(res.recommended_meals, list)
        assert len(res.recommended_meals) > 0
        # ensure meals are from CSV by checking names appear in parsed CSV
        names = [m['name'] for m in res.recommended_meals]
        assert any('tofu' in (n or '').lower() or 'quinoa' in (n or '').lower() or 'salad' in (n or '').lower() for n in names)
    finally:
        db.close()


def test_predict_csv_with_explicit_preference():
    db = ReadSessionLocal()
    try:
        profile = {
            "Age": 45,
            "Gender": "Female",
            "Weight_kg": 65,
            "Height_cm": 165,
            "Physical_Activity_Level": "Light",
        }
        req = PredictRequest(profile=profile, use_csv=True, preference='vegan')
        res = predict(req, db)
        assert isinstance(res.recommended_meals, list)
        assert len(res.recommended_meals) > 0
        # ensure each meal is verified for vegan
        for m in res.recommended_meals:
            assert m.get('verified') is True
    finally:
        db.close()
