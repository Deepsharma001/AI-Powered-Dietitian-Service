"""Database helpers: engines, session factories and DB initialization.

Provides read/write session factories and a simple `init_db` helper that
creates tables and seeds the meals dataset when the DB is empty.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json
from .models import Base, Meal
from data.meals_dataset import MEALS_DATA

# Read/Write partitioning pattern
# In production, set WRITE_DATABASE_URL and READ_DATABASE_URL to different DB instances.
# For SQLite/demo this defaults to the same file but the interfaces are separated.
WRITE_DATABASE_URL = os.getenv("WRITE_DATABASE_URL", "sqlite:///diet.db")
READ_DATABASE_URL = os.getenv("READ_DATABASE_URL", WRITE_DATABASE_URL)

# Engines
write_engine = create_engine(WRITE_DATABASE_URL, connect_args={"check_same_thread": False})
read_engine = create_engine(READ_DATABASE_URL, connect_args={"check_same_thread": False})

# Session factories
WriteSessionLocal = sessionmaker(bind=write_engine)
ReadSessionLocal = sessionmaker(bind=read_engine)


def init_db():
    """Initialize database schema and seed meals.
    
    Creates all tables using SQLAlchemy models and populates the meals
    table with default data if the table is empty.
    """
    Base.metadata.create_all(bind=write_engine)
    session = WriteSessionLocal()
    try:
        count = session.query(Meal).count()
        if count == 0:
            for item in MEALS_DATA:
                m = Meal(
                    name=item['name'],
                    meal_type=item['meal_type'],
                    calories=item['calories'],
                    protein=item['protein'],
                    carbs=item['carbs'],
                    fat=item['fat'],
                    dietary_tags=json.dumps(item.get('dietary_tags', [])),
                    ingredients=json.dumps(item.get('ingredients', [])),
                )
                session.add(m)
            session.commit()
    finally:
        session.close()


# Convenience generators for dependency injection
def get_write_session():
    """Yield a write-enabled SQLAlchemy session for the request scope.

    Use this generator as a FastAPI dependency to ensure the session is
    properly closed after the request completes.
    """
    db = WriteSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_read_session():
    """Yield a read-only SQLAlchemy session for the request scope.

    Used for read endpoints where routing reads to a replica may be desired.
    """
    db = ReadSessionLocal()
    try:
        yield db
    finally:
        db.close()

