"""Content-based recommender service.

Provides a simple content-based recommender which vectorizes meals using
nutritional features (calories, protein, carbs, fat) and binary dietary tags,
then computes cosine similarity to recommend meals similar to a given meal.

This module is intentionally lightweight and used for quick content-based
recommendations before feedback-based models are available.
"""

from typing import List, Tuple
from sqlalchemy.orm import Session
from database import models
from core.logger import get_logger
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json

logger = get_logger("services.content_recommender")


class ContentBasedRecommender:
    """Content-based recommender using nutritional vectors and dietary tags.

    Methods
    -------
    _vectorize_meals(meals)
        Convert a list of Meal objects into a numeric feature matrix and id list.
    recommend_similar(db, meal_id, top_k=5)
        Return a list of (meal_id, score) tuples for the top-k similar meals.
    """

    def __init__(self):
        """Initialize the content-based recommender instance."""
        self.logger = logger

    def _vectorize_meals(self, meals: List[models.Meal]):
        """Convert meals into a numeric feature matrix and corresponding ids.

        The feature matrix rows are composed of normalized numeric features
        (calories, protein, carbs, fat) followed by binary dietary tag features.

        Args:
            meals (List[models.Meal]): List of Meal ORM objects.

        Returns:
            Tuple[numpy.ndarray, List[int]]: A tuple (X, ids) where X is an
            (n_meals, n_features) float array and ids is the list of meal ids.
        """
        all_tags = set()
        parsed = []
        for m in meals:
            tags = []
            try:
                tags = json.loads(m.dietary_tags) if m.dietary_tags else []
            except Exception:
                # fallback if tags stored as string list repr
                try:
                    tags = eval(m.dietary_tags)
                except Exception:
                    tags = []
            parsed.append((m, tags))
            all_tags.update(tags)

        tag_list = sorted(list(all_tags))
        features = []
        ids = []
        for (m, tags) in parsed:
            num_feats = [m.calories or 0.0, m.protein or 0.0, m.carbs or 0.0, m.fat or 0.0]
            tag_feats = [1.0 if t in tags else 0.0 for t in tag_list]
            vec = num_feats + tag_feats
            features.append(vec)
            ids.append(m.id)

        X = np.array(features, dtype=float)
        # normalize numeric columns to unit scale to avoid domination by calories
        if X.shape[0] > 0:
            num_cols = 4
            col_max = X[:, :num_cols].max(axis=0)
            col_max[col_max == 0] = 1.0
            X[:, :num_cols] = X[:, :num_cols] / col_max
        return X, ids

    def recommend_similar(self, db: Session, meal_id: int, top_k: int = 5) -> List[Tuple[int, float]]:
        """Return the top-k most similar meals to the specified meal.

        Similarity is computed using cosine similarity over the feature matrix
        produced by :meth:`_vectorize_meals`. If the `meal_id` is not found or
        there are no meals, an empty list is returned.

        Args:
            db (Session): SQLAlchemy session used to query meals.
            meal_id (int): ID of the meal to find similarities for.
            top_k (int): Maximum number of similar meals to return.

        Returns:
            List[Tuple[int, float]]: Ordered list of (meal_id, score) pairs.
        """
        meals = db.query(models.Meal).all()
        if not meals:
            return []
        X, ids = self._vectorize_meals(meals)
        if meal_id not in ids:
            self.logger.warning("meal_id %s not found for similarity", meal_id)
            return []
        idx = ids.index(meal_id)
        sims = cosine_similarity(X)
        row = sims[idx]
        # get top k excluding self
        ranked = [(ids[i], float(row[i])) for i in range(len(ids)) if i != idx]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


content_recommender = ContentBasedRecommender()
