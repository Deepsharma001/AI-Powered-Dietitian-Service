"""Tests for the diet training and prediction pipeline."""
import os
from services.diet_trainer import train_from_csv, load_model, predict_from_profile
from pathlib import Path

DATA_CSV = "/home/deepak/Downloads/archive/diet_recommendations_dataset.csv"


def test_train_and_predict_quick():
    # Train (this may take a few seconds) and ensure model saved
    res = train_from_csv(DATA_CSV, test_size=0.3)
    assert os.path.exists(res["model_path"]) and res["accuracy"] >= 0.0

    model = load_model()
    assert model is not None

    # pick a minimal profile and ensure predict runs
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

    out = predict_from_profile(profile)
    assert "diet_recommendation" in out and "confidence" in out
