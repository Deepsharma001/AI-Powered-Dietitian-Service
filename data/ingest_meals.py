"""Utilities to ingest meals CSV files into the application's database.

This module provides:
- parse_meals_csv(csv_path): returns a list of normalized meal dicts
- seed_meals_from_csv(csv_path, session): idempotently seeds the meals table

The CSV expected columns include at least `meal_name` and numeric nutrition columns
like `calories`, `protein`, `carbs`, `fat`. Several boolean tag columns are
supported (e.g., `vegan`, `vegetarian`, `keto`, `paleo`, `gluten_free`,
`mediterranean`, `is_healthy`). The parser is resilient to small formatting
issues in the provided fixtures.
"""
from __future__ import annotations

from typing import List, Dict
import logging
import pandas as pd
import math

from database.database import WriteSessionLocal
from database import models

logger = logging.getLogger("data.ingest_meals")

KNOWN_TAGS = {
    "vegan",
    "vegetarian",
    "keto",
    "paleo",
    "gluten_free",
    "mediterranean",
    "is_healthy",
}


def infer_meal_type(name: str) -> str:
    """Heuristic to assign a meal_type from the meal name.
    
    Args:
        name: The name of the meal.
        
    Returns:
        One of 'breakfast', 'lunch', 'dinner', or 'snack'.
    """
    n = (name or "").lower()
    if any(k in n for k in ("pancake", "omelette", "oatmeal", "yogurt", "breakfast")):
        return "breakfast"
    if any(k in n for k in ("salad", "sandwich", "wrap", "bowl", "tofu", "quinoa")):
        return "lunch"
    if any(k in n for k in ("stew", "curry", "steak", "salmon", "dinner", "pizza", "pasta")):
        return "dinner"
    if any(k in n for k in ("snack", "chips", "nuts", "hummus", "edamame", "fruit")):
        return "snack"
    return "lunch"


def _truthy(val) -> bool:
    """Return True for common truthy CSV cell values.
    
    Handles numeric (>= 0.5), boolean, and string representations.
    
    Args:
        val: Value to test for truthiness.
        
    Returns:
        True if value represents truth, False otherwise.
    """
    if val is None:
        return False
    if isinstance(val, (int, float)):
        try:
            return float(val) >= 0.5
        except Exception:
            return False
    v = str(val).strip().lower()
    if v in ("1", "true", "yes", "y"):
        return True
    try:
        return float(v) >= 0.5
    except Exception:
        return False


def parse_meals_csv(csv_path: str) -> List[Dict]:
    """Parse the CSV and return a list of normalized meal dictionaries.
    
    Args:
        csv_path: Path to the meals CSV file.
        
    Returns:
        List of meal dictionaries with keys: name, meal_type, calories,
        protein, carbs, fat, dietary_tags, ingredients.
    """
    logger.info("Parsing meals CSV: %s", csv_path)
    df = pd.read_csv(csv_path, encoding="utf-8", engine="python")
    df = df.rename(columns=lambda s: s.strip())

    meals = []
    for _, row in df.iterrows():
        name = row.get("meal_name") or row.get("name") or row.get("meal")
        if not name or (isinstance(name, float) and math.isnan(name)):
            continue
        name = str(name).strip()

        calories = row.get("calories")
        protein = row.get("protein")
        carbs = row.get("carbs")
        fat = row.get("fat")
        try:
            calories = float(calories) if not (calories is None or str(calories).strip() == "") else 0.0
        except Exception:
            calories = 0.0
        for k in ("protein", "carbs", "fat"):
            try:
                locals()[k] = float(row.get(k)) if not (row.get(k) is None or str(row.get(k)).strip() == "") else 0.0
            except Exception:
                locals()[k] = 0.0

        # Build tags
        tags = []
        for t in KNOWN_TAGS:
            if t in row.index and _truthy(row.get(t)):
                tags.append(t)

        # fallback: check for an 'is_healthy' or 'healthy' column with floating score
        if ("is_healthy" in row.index and _truthy(row.get("is_healthy"))) and "is_healthy" not in tags:
            tags.append("is_healthy")

        meal_type = infer_meal_type(name)

        ingredients = []
        # if 'ingredients' column exists, try to parse a JSON-like or comma-separated list
        if "ingredients" in row.index and row.get("ingredients"):
            raw = str(row.get("ingredients"))
            try:
                import json

                ingredients = json.loads(raw)
            except Exception:
                ingredients = [i.strip() for i in raw.split(",") if i.strip()]

        meals.append({
            "name": name,
            "meal_type": meal_type,
            "calories": round(calories, 2),
            "protein": round(float(row.get("protein") or protein or 0.0), 2),
            "carbs": round(float(row.get("carbs") or carbs or 0.0), 2),
            "fat": round(float(row.get("fat") or fat or 0.0), 2),
            "dietary_tags": tags,
            "ingredients": ingredients,
        })

    logger.info("Parsed %s meals from CSV", len(meals))
    return meals


def seed_meals_from_csv(csv_path: str, session=None):
    """Idempotently seed the meals table from the CSV file.

    If `session` is not supplied, a `WriteSessionLocal` session is used.
    Existing meals are matched by name and skipped to avoid duplicates.
    
    Args:
        csv_path: Path to the meals CSV file.
        session: Optional SQLAlchemy session. If None, creates a new one.
        
    Returns:
        Dictionary with 'added' (count of new meals) and 'total' (final count).
    """
    close_session = False
    if session is None:
        session = WriteSessionLocal()
        close_session = True
    try:
        parsed = parse_meals_csv(csv_path)
        added = 0
        for item in parsed:
            existing = session.query(models.Meal).filter(models.Meal.name == item["name"]).first()
            if existing:
                continue
            m = models.Meal(
                name=item["name"],
                meal_type=item["meal_type"],
                calories=item["calories"],
                protein=item["protein"],
                carbs=item["carbs"],
                fat=item["fat"],
                dietary_tags="[" + ", ".join(f'"{t}"' for t in item.get("dietary_tags", [])) + "]",
                ingredients="[]" if not item.get("ingredients") else str(item.get("ingredients")),
            )
            session.add(m)
            added += 1
        if added:
            session.commit()
        logger.info("Seeded %s new meals into DB", added)
        return added
    finally:
        if close_session:
            session.close()


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser("Seed meals from CSV into the DB")
    p.add_argument("csv_path", nargs="?", default="data/fixtures/healthy_meal_plans.csv")
    args = p.parse_args()
    seed_meals_from_csv(args.csv_path)
    print("Done")
