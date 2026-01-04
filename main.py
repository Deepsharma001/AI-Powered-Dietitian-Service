"""Application entry point for the Diet Recommendation API.

Defines FastAPI app, middleware, exception handlers and includes API
routers from the `api` package. The `lifespan` handler initializes the DB
on startup.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List, Optional
import json
from contextlib import asynccontextmanager

from database import init_db, models
from schemas import UserCreateRequest, UserWithMealPlanResponse, AllUsersResponse, MealDetail
from core.exceptions import DatabaseError
import services.recommendation_engine as re

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Fastapi lifespan context: initialize resources before serving requests."""
    # Initialize database on startup
    init_db()
    yield


app = FastAPI(title="Diet Recommendation API", version="1.0.0", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from database.deps import get_db_read, get_db_write
from core.logger import get_logger
from core.error_handlers import register_exception_handlers
from fastapi import Request
from fastapi.responses import JSONResponse
from api.users import router as users_router
from api.meals import router as meals_router
from api.recommendations import router as recommendations_router
from api.train import router as train_router

logger = get_logger("main")

# Register exception handlers
register_exception_handlers(app)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests and their responses."""
    logger.info("%s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
        logger.info("%s %s -> %s", request.method, request.url.path, response.status_code)
        return response
    except Exception as exc:
        logger.exception("Request error: %s %s", request.method, request.url.path)
        raise


@app.get("/health")
def health(db: Session = Depends(get_db_read)):
    """Return basic health status and database connectivity.
    
    Raises:
        DatabaseError: If database connection fails.
    """
    try:
        _ = db.query(models.Meal).first()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.exception("Health check failed")
        raise DatabaseError("Database health check failed", details={"error": str(e)})


# include routers
app.include_router(users_router)
app.include_router(meals_router)
app.include_router(recommendations_router)
app.include_router(train_router)


if __name__ == "__main__":
    # Allow starting the app via `python ./main.py`
    try:
        import uvicorn
    except Exception as exc:
        raise RuntimeError("uvicorn is required to run the app. Install with `pip install uvicorn[standard]`. Error: %s" % exc)

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

