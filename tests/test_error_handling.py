"""Test error handling functionality.

Verifies that custom exceptions are properly raised and handled,
returning appropriate error responses.
"""
import pytest
from database import init_db
from database.database import ReadSessionLocal, WriteSessionLocal
from core.exceptions import NotFoundError, ValidationError, ModelNotTrainedError
from api.recommendations import submit_feedback, get_similar_meals
from api.train import predict
from schemas.feedback_schema import FeedbackCreateRequest
from schemas.diet_schema import PredictRequest


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Initialize database before tests."""
    init_db()


def test_user_not_found_raises_404():
    """Test that requesting non-existent user raises NotFoundError."""
    db = WriteSessionLocal()
    try:
        with pytest.raises(NotFoundError) as exc_info:
            payload = FeedbackCreateRequest(user_id=99999, meal_id=1, rating=5)
            submit_feedback(plan_id=1, payload=payload, db=db)
        assert "User" in str(exc_info.value.message)
        assert exc_info.value.status_code == 404
    finally:
        db.close()


def test_meal_not_found_raises_404():
    """Test that requesting non-existent meal raises NotFoundError."""
    db = ReadSessionLocal()
    try:
        with pytest.raises(NotFoundError) as exc_info:
            get_similar_meals(meal_id=99999, top_k=5, db=db)
        assert "Meal" in str(exc_info.value.message)
        assert exc_info.value.status_code == 404
    finally:
        db.close()


def test_predict_without_params_raises_validation_error():
    """Test that predict endpoint requires user_id or profile."""
    db = ReadSessionLocal()
    try:
        with pytest.raises(ValidationError) as exc_info:
            req = PredictRequest()
            predict(request=req, db=db)
        assert "user_id" in str(exc_info.value.message).lower() or "profile" in str(exc_info.value.message).lower()
        assert exc_info.value.status_code == 400
    finally:
        db.close()


def test_exception_classes_have_proper_attributes():
    """Test that custom exception classes have expected attributes."""
    # Test NotFoundError
    exc = NotFoundError("User", 123)
    assert exc.status_code == 404
    assert "User" in exc.message
    assert "123" in exc.message
    
    # Test ValidationError
    exc = ValidationError("Invalid input", field="age")
    assert exc.status_code == 400
    assert exc.message == "Invalid input"
    assert exc.details == {"field": "age"}
    
    # Test ModelNotTrainedError
    exc = ModelNotTrainedError()
    assert exc.status_code == 503
    assert "train" in exc.message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

