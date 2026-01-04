"""Unit tests for the content-based recommender."""

from services.content_recommender import ContentBasedRecommender


class DummyMeal:
    """Simple stand-in object mimicking the Meal ORM fields used by the recommender."""
    def __init__(self, id, name, calories, protein, carbs, fat, tags):
        """Create a dummy meal with minimal nutritional fields."""
        self.id = id
        self.name = name
        self.calories = calories
        self.protein = protein
        self.carbs = carbs
        self.fat = fat
        self.dietary_tags = str(tags)
        self.ingredients = '[]'


class DummyDB:
    """Minimal DB wrapper that returns a list of dummy meals for queries."""
    def __init__(self, meals):
        self._meals = meals

    def query(self, model):
        class Q:
            def __init__(self, meals):
                self._meals = meals

            def all(self):
                return self._meals

        return Q(self._meals)


def test_recommend_similar_basic():
    """Verify the recommender returns expected similar meals in a simple case."""
    m1 = DummyMeal(1, 'A', 400, 20, 40, 10, ['vegetarian'])
    m2 = DummyMeal(2, 'B', 410, 21, 42, 11, ['vegetarian'])
    m3 = DummyMeal(3, 'C', 800, 50, 90, 30, ['nonveg'])
    db = DummyDB([m1, m2, m3])
    rec = ContentBasedRecommender()
    ranked = rec.recommend_similar(db, meal_id=1, top_k=2)
    # expect meal 2 to be most similar to 1
    assert len(ranked) == 2
    assert ranked[0][0] == 2
