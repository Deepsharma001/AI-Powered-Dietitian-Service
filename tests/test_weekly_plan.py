"""Test weekly meal plan generation."""
from services.recommendation_engine import recommendation_service
from database.database import ReadSessionLocal
from database import init_db, models
from schemas.diet_schema import PredictRequest
from api.train import predict
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Initialize database before tests."""
    init_db()


def test_weekly_plan_generates_seven_days():
    """Test that weekly plan generation creates 7 days of meals."""
    db = ReadSessionLocal()
    try:
        user = db.query(models.User).first()
        if not user:
            pytest.skip("No users in database")
        
        all_meals = db.query(models.Meal).all()
        if not all_meals:
            pytest.skip("No meals in database")
        
        weekly = recommendation_service.generate_weekly_meal_plan(user, all_meals)
        
        assert len(weekly) == 7, "Should generate 7 days"
        
        # Check each day has required structure
        for day in weekly:
            assert 'date' in day
            assert 'day_of_week' in day
            assert 'breakfast' in day
            assert 'lunch' in day
            assert 'dinner' in day
            assert 'daily_totals' in day
            
            # Check daily totals
            assert day['daily_totals']['calories'] > 0
            assert day['daily_totals']['protein'] > 0
    finally:
        db.close()


def test_weekly_plan_has_variety():
    """Test that weekly plan provides meal variety."""
    db = ReadSessionLocal()
    try:
        user = db.query(models.User).first()
        if not user:
            pytest.skip("No users in database")
        
        all_meals = db.query(models.Meal).all()
        if not all_meals:
            pytest.skip("No meals in database")
        
        weekly = recommendation_service.generate_weekly_meal_plan(user, all_meals)
        
        # Collect snack IDs across the week
        snack_ids = [day.get('snack', {}).get('id') for day in weekly if day.get('snack')]
        
        # Check for variety in snacks (should have at least 2 different snacks if enough available)
        if len(snack_ids) >= 2:
            unique_snacks = len(set(snack_ids))
            assert unique_snacks > 1, "Weekly plan should have variety in snacks"
    finally:
        db.close()


def test_predict_with_weekly_flag():
    """Test that predict endpoint with weekly=True returns weekly plan."""
    db = ReadSessionLocal()
    try:
        profile = {
            "Age": 30,
            "Gender": "Male",
            "Weight_kg": 75,
            "Height_cm": 175,
            "Physical_Activity_Level": "Moderate",
        }
        
        req = PredictRequest(profile=profile, weekly=True)
        res = predict(request=req, db=db)
        
        assert res.weekly_plan is not None, "Should return weekly_plan"
        assert res.daily_plan is None, "Should not return daily_plan when weekly=True"
        assert len(res.weekly_plan) == 7, "Weekly plan should have 7 days"
        
        # Check first day structure
        day1 = res.weekly_plan[0]
        assert 'breakfast' in day1
        assert 'lunch' in day1
        assert 'dinner' in day1
        assert 'daily_totals' in day1
        assert 'day_of_week' in day1
    finally:
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
