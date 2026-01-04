"""Tests for the CSV ingestion utilities in `data/ingest_meals.py`."""
from data.ingest_meals import parse_meals_csv, seed_meals_from_csv
from database.database import ReadSessionLocal
from database import models


def test_parse_meals_csv_has_expected_keys():
    rows = parse_meals_csv("data/fixtures/healthy_meal_plans.csv")
    assert isinstance(rows, list) and len(rows) > 0
    first = rows[0]
    assert "name" in first and "calories" in first and "dietary_tags" in first


def test_seed_meals_is_idempotent():
    session = ReadSessionLocal()
    try:
        before = session.query(models.Meal).count()
        added = seed_meals_from_csv("data/fixtures/healthy_meal_plans.csv", session=session)
        after = session.query(models.Meal).count()
        assert after >= before
        # Run again - should not duplicate
        added2 = seed_meals_from_csv("data/fixtures/healthy_meal_plans.csv", session=session)
        after2 = session.query(models.Meal).count()
        assert after2 == after
    finally:
        session.close()
