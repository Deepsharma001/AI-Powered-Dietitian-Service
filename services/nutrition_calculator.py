"""Nutrition calculation helpers.

Provides BMI/BMR/TDEE and macro allocation utilities used by the app.
"""

from typing import Dict
from core.logger import get_logger

logger = get_logger("services.nutrition_calculator")

class NutritionCalculator:
    """Class-based nutrition calculator used across the app."""

    def calculate_bmi(self, height_cm: float, weight_kg: float) -> float:
        """Calculate BMI from height in cm and weight in kg."""
        h_m = height_cm / 100.0
        if h_m <= 0:
            return 0.0
        return weight_kg / (h_m * h_m)

    def calculate_bmr(self, age: int, height_cm: float, weight_kg: float, gender: str) -> float:
        """Calculate BMR using Mifflin-St Jeor approximation."""
        if gender.lower() == 'male':
            return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    def calculate_tdee(self, bmr: float, activity_level: str) -> float:
        """Estimate TDEE from BMR and activity multiplier."""
        mapping = {
            'sedentary': 1.2,
            'lightly_active': 1.375,
            'moderately_active': 1.55,
            'very_active': 1.725,
            'extremely_active': 1.9
        }
        val = bmr * mapping.get(activity_level, 1.2)
        logger.debug("TDEE calculated: %s", val)
        return val

    def calculate_target_calories(self, tdee: float, health_goal: str) -> float:
        """Derive a daily calorie target from TDEE based on a health goal."""
        if health_goal == 'weight_loss':
            val = max(1200, tdee - 500)
        elif health_goal == 'muscle_gain':
            val = tdee + 300
        else:
            val = tdee
        logger.debug("Target calories for goal %s: %s", health_goal, val)
        return val

    def calculate_macros(self, target_calories: float, dietary_preference: str) -> Dict[str, float]:
        """Allocate macronutrient targets (grams) from a calorie target.

        Supports simple presets for 'keto' and 'high-protein' preferences.
        """
        if dietary_preference == 'keto':
            ratios = {'protein': 0.3, 'carbs': 0.1, 'fat': 0.6}
        elif dietary_preference == 'high-protein':
            ratios = {'protein': 0.4, 'carbs': 0.3, 'fat': 0.3}
        else:
            ratios = {'protein': 0.3, 'carbs': 0.4, 'fat': 0.3}
        protein_g = (target_calories * ratios['protein']) / 4
        carbs_g = (target_calories * ratios['carbs']) / 4
        fat_g = (target_calories * ratios['fat']) / 9
        macros = {'protein': round(protein_g), 'carbs': round(carbs_g), 'fat': round(fat_g)}
        logger.debug("Macros calculated: %s", macros)
        return macros


# export singleton
nutrition_calculator = NutritionCalculator()
__all__ = ["NutritionCalculator", "nutrition_calculator"]
