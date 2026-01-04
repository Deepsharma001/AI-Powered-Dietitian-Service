"""Recommendation engine service.

Provides heuristics to compute nutrition targets and to select meals that
match a user's dietary preferences and goals.
"""

from typing import List, Dict, Optional
import math
import random
import json
from core.logger import get_logger

logger = get_logger("services.recommendation_engine")

class RecommendationEngine:
    """Class-based recommendation engine for meal selection."""

    def __init__(self, variety_weight: float = 0.3):
        """Initialize the recommendation engine.

        Parameters
        ----------
        variety_weight: float
            Weighting factor controlling how much variety is favored in selections.
        """
        self.variety_weight = variety_weight

    # Nutrition calculations (optional helpers, keep lightweight)
    def calculate_bmi(self, height_cm: float, weight_kg: float) -> float:
        """Calculate Body Mass Index (BMI) from height and weight.
        
        Args:
            height_cm: Height in centimeters.
            weight_kg: Weight in kilograms.
            
        Returns:
            BMI value as a float.
        """
        h_m = height_cm / 100.0
        if h_m <= 0:
            return 0.0
        return weight_kg / (h_m * h_m)

    def calculate_bmr(self, age: int, height_cm: float, weight_kg: float, gender: str) -> float:
        """Calculate Basal Metabolic Rate (BMR) using Mifflin-St Jeor equation.
        
        Args:
            age: Age in years.
            height_cm: Height in centimeters.
            weight_kg: Weight in kilograms.
            gender: Gender ('male' or 'female').
            
        Returns:
            BMR value in calories per day.
        """
        if gender.lower() == 'male':
            return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    def calculate_tdee(self, bmr: float, activity_level: str) -> float:
        """Estimate Total Daily Energy Expenditure (TDEE) from BMR.
        
        Args:
            bmr: Basal Metabolic Rate.
            activity_level: Activity level string (e.g., 'sedentary', 'moderately_active').
            
        Returns:
            TDEE value in calories per day.
        """
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
        """Apply goal-based adjustment to set daily target calories.
        
        Args:
            tdee: Total Daily Energy Expenditure.
            health_goal: Goal string ('weight_loss', 'muscle_gain', 'maintain').
            
        Returns:
            Adjusted target calories per day.
        """
        if health_goal == 'weight_loss':
            val = max(1200, tdee - 500)
        elif health_goal == 'muscle_gain':
            val = tdee + 300
        else:
            val = tdee
        logger.debug("Target calories for goal %s: %s", health_goal, val)
        return val

    def calculate_macros(self, target_calories: float, dietary_preference: str) -> Dict[str, float]:
        """Convert target calories into gram-based macronutrient targets.
        
        Args:
            target_calories: Daily calorie target.
            dietary_preference: Preference string ('keto', 'high-protein', etc.).

        Returns:
            Dictionary with rounded gram targets for 'protein', 'carbs', 'fat'.
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

    # Meal selection utilities
    def filter_meals_by_preference(self, all_meals: List, dietary_preference: str, allergies: Optional[List[str]] = None) -> List:
        """Filter a list of Meal objects by dietary preference and allergies.

        Args:
            all_meals: Iterable of meal ORM objects.
            dietary_preference: A string tag (e.g., 'vegetarian', 'keto').
            allergies: Optional list of ingredient substrings to exclude.

        Returns:
            List of Meal objects that match the given preference and do not
            contain listed allergy ingredients.
        """
        out = []
        for m in all_meals:
            # robustly parse tags/ingredients whether stored as JSON strings or Python lists
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
            ingredients = []
            if hasattr(m, 'ingredients'):
                if isinstance(m.ingredients, (list, tuple)):
                    ingredients = [str(i).lower() for i in m.ingredients]
                else:
                    try:
                        ingredients = [str(i).lower() for i in json.loads(m.ingredients)]
                    except Exception:
                        try:
                            ingredients = [str(i).lower() for i in eval(m.ingredients)]
                        except Exception:
                            ingredients = []

            if dietary_preference and dietary_preference != 'none':
                if dietary_preference not in tags and dietary_preference != 'high-protein':
                    continue
            if allergies:
                if any(a.lower() in (ing for ing in ingredients) for a in allergies):
                    continue
            out.append(m)
        logger.debug("Filtered meals: %s -> %s", len(all_meals), len(out))
        return out

    def score_meal(self, meal, target_calories_per_meal: float, target_macros_per_meal: Dict[str, float]) -> float:
        """Compute a heuristic score for how well a meal matches targets.

        Score blends calories proximity and macro proximity penalty.
        
        Args:
            meal: Meal object to score.
            target_calories_per_meal: Target calories for this meal slot.
            target_macros_per_meal: Target macros dict (protein, carbs, fat).
            
        Returns:
            Float score where higher values indicate better matches.
        """
        cal_diff = abs(meal.calories - target_calories_per_meal)
        cal_score = max(0, 50 - (cal_diff / max(1, target_calories_per_meal)) * 50)
        p_diff = abs(meal.protein - target_macros_per_meal['protein'])
        c_diff = abs(meal.carbs - target_macros_per_meal['carbs'])
        f_diff = abs(meal.fat - target_macros_per_meal['fat'])
        denom = (target_macros_per_meal['protein'] + target_macros_per_meal['carbs'] + max(1, target_macros_per_meal['fat']))
        macro_penalty = (p_diff + c_diff + f_diff) / denom
        macro_score = max(0, 40 - macro_penalty * 40)
        score = cal_score + macro_score + random.random()
        logger.debug("Score meal %s: %s", getattr(meal, 'name', None), score)
        return score

    def select_best_meal(self, meals_pool: List, meal_type: str, target_calories: float, target_macros: Dict[str, float]):
        """Select the highest-scoring meal matching a given meal_type.
        
        Args:
            meals_pool: Pool of candidate meal objects.
            meal_type: Required meal type ('breakfast', 'lunch', 'dinner', 'snack').
            target_calories: Target calories for this meal slot.
            target_macros: Target macros dict.

        Returns:
            Best matching Meal object or None if no candidates found.
        """
        candidates = [m for m in meals_pool if m.meal_type == meal_type]
        if not candidates:
            logger.warning("No candidates for meal_type %s", meal_type)
            return None
        best = max(candidates, key=lambda m: self.score_meal(m, target_calories, target_macros))
        logger.debug("Selected best meal for %s: %s", meal_type, best.name)
        return best

    def generate_daily_meal_plan(self, user_profile, all_meals) -> Dict:
        """Generate a daily meal plan tailored to the given user profile.

        The plan divides target calories and macros across meal types and picks
        the best-fitting meal per slot using internal heuristics.

        Args:
            user_profile: ORM User object containing target calories/macros.
            all_meals: Iterable of Meal objects available for selection.

        Returns:
            A dictionary with meal entries and daily totals.
        """
        target_calories = user_profile.target_calories
        per = {'breakfast': 0.25, 'lunch': 0.35, 'dinner': 0.35, 'snack': 0.05}
        total_macros = {'protein': user_profile.target_protein, 'carbs': user_profile.target_carbs, 'fat': user_profile.target_fat}

        allergies = []
        try:
            allergies = json.loads(user_profile.allergies) if user_profile.allergies else []
        except Exception:
            allergies = []
        pool = self.filter_meals_by_preference(all_meals, user_profile.dietary_preference, allergies)

        plan = {}
        daily_totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
        for mtype in ['breakfast', 'lunch', 'dinner', 'snack']:
            target_c = target_calories * per[mtype]
            target_mac = {k: total_macros[k] * per[mtype] for k in total_macros}
            sel = self.select_best_meal(pool, mtype, target_c, target_mac)
            if sel is None:
                candidates = [m for m in all_meals if getattr(m, 'meal_type', None) == mtype]
                if not candidates:
                    continue
                sel = random.choice(candidates)
            plan[mtype] = {
                'id': getattr(sel, 'id', None),
                'name': getattr(sel, 'name', None),
                'meal_type': getattr(sel, 'meal_type', None),
                'calories': getattr(sel, 'calories', 0),
                'protein': getattr(sel, 'protein', 0),
                'carbs': getattr(sel, 'carbs', 0),
                'fat': getattr(sel, 'fat', 0),
                'ingredients': json.loads(sel.ingredients) if hasattr(sel, 'ingredients') and sel.ingredients else []
            }
            daily_totals['calories'] += getattr(sel, 'calories', 0)
            daily_totals['protein'] += getattr(sel, 'protein', 0)
            daily_totals['carbs'] += getattr(sel, 'carbs', 0)
            daily_totals['fat'] += getattr(sel, 'fat', 0)

        plan['daily_totals'] = daily_totals
        plan['date'] = __import__('datetime').date.today().isoformat()
        logger.info("Generated plan for user %s: calories=%s", getattr(user_profile, 'id', None), daily_totals['calories'])
        return plan


# export a default instance
recommendation_service = RecommendationEngine()
