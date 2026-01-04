"""SQLAlchemy ORM models for the diet recommendation service.

This module defines the database schema models used throughout the
application: User, Meal, MealPlan and Feedback. Models are simple SQLAlchemy
declarative classes and intentionally keep behavior-free (no business logic).
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    """ORM model representing an application user.

    Attributes correspond to user profile and calculated nutrition targets.
    """

    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    height = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    gender = Column(String, nullable=False)
    activity_level = Column(String, nullable=False)
    dietary_preference = Column(String, nullable=False)
    health_goal = Column(String, nullable=False)
    allergies = Column(Text, nullable=True)
    target_calories = Column(Float, nullable=True)
    target_protein = Column(Float, nullable=True)
    target_carbs = Column(Float, nullable=True)
    target_fat = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Meal(Base):
    """ORM model representing an individual meal option.

    Dietary tags and ingredients are stored as JSON-encoded strings.
    """

    __tablename__ = "meals"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    meal_type = Column(String, nullable=False)
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    dietary_tags = Column(Text, nullable=True)
    ingredients = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MealPlan(Base):
    """ORM model representing a generated meal plan for a user on a date."""

    __tablename__ = "meal_plans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    plan_date = Column(DateTime, nullable=False)
    breakfast_id = Column(Integer, ForeignKey('meals.id'))
    lunch_id = Column(Integer, ForeignKey('meals.id'))
    dinner_id = Column(Integer, ForeignKey('meals.id'))
    snack_id = Column(Integer, ForeignKey('meals.id'), nullable=True)
    total_calories = Column(Float)
    total_protein = Column(Float)
    total_carbs = Column(Float)
    total_fat = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    """ORM model storing user feedback (ratings) for meals within a plan."""

    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    plan_id = Column(Integer, ForeignKey('meal_plans.id'), nullable=True)
    meal_id = Column(Integer, ForeignKey('meals.id'), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    created_at = Column(DateTime, default=datetime.utcnow)
