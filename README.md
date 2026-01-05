# AI-Powered Dietitian Service

An intelligent FastAPI-based backend service that generates personalized diet and meal recommendations using machine learning, nutrition science, and content-based filtering.

## Table of Contents

- [Features](#-features)
- [Dataset](#-dataset)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Setup Instructions](#-setup-instructions)
- [API Endpoints](#-api-endpoints)
- [Project Structure](#-project-structure)
- [Approach & Methodology](#-approach--methodology)
- [Testing](#-testing)
- [Documentation](#-documentation)

## Features

- **Personalized Meal Plans** - Generate daily and weekly meal plans tailored to user profiles
- **ML-Powered Predictions** - RandomForest classifier predicts optimal diet types
- **Nutrition Calculation** - BMI, BMR, TDEE, and macro nutrient calculations
- **Content-Based Recommendations** - TF-IDF and cosine similarity for meal suggestions
- **Dietary Preferences** - Support for vegetarian, vegan, keto, paleo, etc.
- **CSV & Database Sources** - Flexible meal sourcing from fixtures or database
- **User Feedback System** - Collect ratings for collaborative filtering
- **Comprehensive Error Handling** - Custom exceptions with standardized responses
- **Repository Pattern** - Clean data access layer with CRUD operations

## Dataset

The service uses two datasets sourced from Kaggle:

1. **Diet Recommendations Dataset** - Used for training the ML model
   - Contains user profiles with age, gender, weight, height, activity level, and recommended diet types
   - Used to train the RandomForest classifier for diet prediction
   
2. **Healthy Meal Plans Dataset** - Meal database with nutritional information
   - Contains 500+ meals with complete nutritional profiles
   - Includes meal types (breakfast, lunch, dinner, snack), calories, macros, and dietary tags
   - Located at: `data/fixtures/healthy_meal_plans.csv`

**Source**: [Kaggle Datasets](https://www.kaggle.com/)

## Tech Stack

### Core Framework
- **FastAPI** - Modern async web framework
- **Pydantic v2** - Data validation and serialization
- **SQLAlchemy** - ORM for database operations
- **SQLite** - Lightweight database

### Machine Learning
- **scikit-learn** - RandomForest classifier with preprocessing pipeline
- **pandas & numpy** - Data manipulation and analysis
- **TF-IDF Vectorizer** - Text feature extraction for content recommendations

### Development
- **pytest** - Testing framework
- **uvicorn** - ASGI server
- **python-dotenv** - Environment configuration

## Architecture

The service follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│              FastAPI Application Layer              │
│  (main.py, API routers, middleware, error handlers) │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────┐
│                  API Layer (api/)                   │
│  users.py, meals.py, recommendations.py, train.py   │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────┐
│               Services Layer (services/)             │
│  recommendation_engine, content_recommender,         │
│  nutrition_calculator, diet_trainer                  │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────┐
│           Core & Data Layer (core/, data/)          │
│  repository, exceptions, error_handlers, logger,     │
│  database models, meal ingestion                     │
└──────────────────────────────────────────────────────┘
```

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AI-Powered-Dietitian-Service
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # On Linux/Mac
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database and load meal data**
   ```bash
   python -c "from database import init_db; init_db()"
   python -c "from data.ingest_meals import seed_meals_from_csv; seed_meals_from_csv('data/fixtures/healthy_meal_plans.csv')"
   ```

5. **Train the ML model** (Optional - model trains on first prediction if not done)
   ```bash
   # Place your training dataset at the path below or update the path
   python -c "from services.diet_trainer import train_from_csv; train_from_csv('/home/deepak/Downloads/archive/diet_recommendations_dataset.csv')"
   ```

6. **Run the server**
   ```bash
   # Development mode with auto-reload
   python main.py
   
   # Or using uvicorn directly
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **Access the API**
   - API Base URL: `http://localhost:8000`
   - Interactive Docs: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/health`

## API Endpoints

### Health & Status
- `GET /health` - Health check and database connectivity

### User Management
- `POST /api/create-user-with-plan` - Create user and generate initial meal plan
- `GET /api/users-with-plans` - List all users with their latest meal plans

### Diet Prediction
- `POST /api/diet/train` - Train the ML model from CSV
- `POST /api/diet/predict` - Predict diet recommendation for user profile

### Meal Recommendations
- `POST /api/recommendations/{plan_id}/feedback` - Submit meal feedback/rating
- `GET /api/recommendations/meal/{meal_id}/similar` - Get similar meals

### Meal Management
- `GET /api/meals` - List all available meals

### Example Request

```bash
# Create user with meal plan (balanced diet, maintenance goal)
curl -X POST "http://localhost:8000/api/create-user-with-plan" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "age": 30,
    "height": 175,
    "weight": 75,
    "gender": "male",
    "activity_level": "moderately_active",
    "dietary_preference": "balanced",
    "health_goal": "maintain"
  }'

# Create user with weight loss goal and vegetarian preference
curl -X POST "http://localhost:8000/api/create-user-with-plan" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "age": 28,
    "height": 165,
    "weight": 70,
    "gender": "female",
    "activity_level": "lightly_active",
    "dietary_preference": "vegetarian",
    "health_goal": "weight_loss",
    "use_csv": true
  }'

# Create user with muscle gain goal
curl -X POST "http://localhost:8000/api/create-user-with-plan" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mike Johnson",
    "age": 25,
    "height": 180,
    "weight": 85,
    "gender": "male",
    "activity_level": "very_active",
    "dietary_preference": "high-protein",
    "health_goal": "muscle_gain"
  }'

# Predict diet with CSV meals
curl -X POST "http://localhost:8000/api/diet/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "use_csv": true,
    "preference": "veg"
  }'
```

### Available Options

**Health Goals:**
- `weight_loss` - Reduces daily calories by 500 (minimum 1200)
- `muscle_gain` - Increases daily calories by 300
- `maintain` - Maintains current TDEE

**Dietary Preferences:**
- `balanced` - Standard 30/40/30 (protein/carbs/fat) ratio
- `keto` - Low-carb, high-fat diet
- `vegetarian` - Excludes meat
- `vegan` - Excludes all animal products
- `paleo` - Whole foods, no processed items
- `mediterranean` - Heart-healthy Mediterranean diet
- `high-protein` - 40% protein, 30/30 carbs/fat

**Activity Levels:**
- `sedentary` - Little to no exercise
- `lightly_active` - Exercise 1-3 days/week
- `moderately_active` - Exercise 3-5 days/week
- `very_active` - Exercise 6-7 days/week
- `extremely_active` - Very intense daily exercise

## Project Structure

```
AI-Powered-Dietitian-Service/
├── api/                          # API route handlers
│   ├── users.py                  # User and meal plan endpoints
│   ├── meals.py                  # Meal listing endpoints
│   ├── recommendations.py        # Feedback and similar meals
│   └── train.py                  # ML training and prediction
├── core/                         # Core utilities
│   ├── exceptions.py             # Custom exception classes
│   ├── error_handlers.py         # FastAPI exception handlers
│   ├── logger.py                 # Logging configuration
│   └── repository.py             # Repository pattern for DB operations
├── data/                         # Data layer
│   ├── ingest_meals.py           # CSV meal ingestion utilities
│   ├── fixtures/                 # Meal data fixtures
│   │   └── healthy_meal_plans.csv
│   └── models/                   # Trained ML models
│       └── diet_model.joblib
├── database/                     # Database layer
│   ├── database.py               # Session management
│   ├── deps.py                   # Dependency injection
│   ├── models.py                 # SQLAlchemy ORM models
│   └── models_feedback.py        # Feedback model
├── schemas/                      # Pydantic schemas
│   ├── diet_schema.py            # Diet prediction schemas
│   ├── user_schema.py            # User schemas
│   ├── meal_schema.py            # Meal schemas
│   ├── recommendation_schema.py  # Recommendation schemas
│   └── feedback_schema.py        # Feedback schemas
├── services/                     # Business logic
│   ├── recommendation_engine.py  # Meal plan generation
│   ├── content_recommender.py    # Content-based filtering
│   ├── nutrition_calculator.py   # BMI, BMR, TDEE calculations
│   └── diet_trainer.py           # ML model training/prediction
├── tests/                        # Test suite
│   ├── test_error_handling.py    # Error handling tests
│   ├── test_predict_api.py       # Prediction API tests
│   ├── test_diet_trainer.py      # ML model tests
│   └── test_content_recommender.py
├── logs/                         # Application logs
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore patterns
├── ERROR_HANDLING.md             # Error handling documentation
├── ERROR_HANDLING_FLOW.md        # Error flow diagram
└── README.md                     # This file
```

## Approach & Methodology

### 1. Nutrition Science Foundation

The service uses established nutrition formulas:

- **BMI (Body Mass Index)**: `weight(kg) / (height(m))²`
- **BMR (Basal Metabolic Rate)**: Mifflin-St Jeor Equation
  - Men: `10 × weight + 6.25 × height - 5 × age + 5`
  - Women: `10 × weight + 6.25 × height - 5 × age - 161`
- **TDEE (Total Daily Energy Expenditure)**: `BMR × activity_multiplier`
- **Target Calories**: Adjusted based on health goals (lose/gain/maintain)
- **Macros**: Protein/Carbs/Fat ratios based on dietary preferences

### 2. Machine Learning Pipeline

**Training Process:**
1. Load diet recommendation dataset (CSV with user profiles and diet labels)
2. Preprocess features (numeric imputation, categorical encoding)
3. Train RandomForest classifier with ColumnTransformer pipeline
4. Persist model using joblib for fast loading

**Prediction Process:**
1. Accept user profile (age, gender, weight, height, activity level)
2. Transform features through trained pipeline
3. Predict optimal diet type with confidence scores
4. Filter meals matching predicted diet preference

### 3. Recommendation Engine

**Daily Meal Plan Generation:**
1. Calculate user's nutritional targets (calories, macros)
2. Filter meals by dietary preferences and allergies
3. Score each meal based on:
   - Calorie proximity to per-meal target
   - Macro nutrient balance
   - Dietary preference alignment
4. Select optimal breakfast, lunch, dinner, and snack
5. Validate total daily nutrition meets targets

**Content-Based Filtering:**
1. Extract meal features (ingredients, dietary tags, nutrients)
2. Build TF-IDF vectors from text features
3. Calculate cosine similarity between meals
4. Return top-k most similar meals for variety

### 4. Data Architecture

**Repository Pattern:**
- Abstraction layer over SQLAlchemy
- Generic `BaseRepository<T>` with CRUD operations
- `save()` and `save_all()` helpers eliminate boilerplate
- Supports both read and write sessions

**Dual Data Sources:**
- **Database**: Persistent meal storage with full CRUD
- **CSV Fixtures**: Quick meal sourcing for development/testing
- Transparent switching via `use_csv` flag

### 5. Error Handling Strategy

**Custom Exception Hierarchy:**
- `AppException` base with status codes and details
- Domain-specific exceptions (NotFoundError, ValidationError, etc.)
- Centralized handlers convert to standardized JSON
- Comprehensive logging without exposing internals

**Benefits:**
- Consistent API responses across all endpoints
- Clear error messages with actionable guidance
- Proper HTTP status codes (400, 404, 422, 500, 503)
- Enhanced debugging with contextual details

### 6. API Design Principles

- **RESTful conventions** for resource naming
- **Dependency injection** for database sessions
- **Read/write session separation** for performance
- **Pydantic validation** for request/response schemas
- **Comprehensive docstrings** for all functions
- **OpenAPI/Swagger** documentation auto-generated

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_error_handling.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

**Test Coverage:**
- ML model training and prediction
- Content-based recommendations
- CSV meal ingestion
- API endpoints with various scenarios
- Error handling for edge cases

**Current Status:** 12/12 tests passing ✅

## Documentation

- **[ERROR_HANDLING.md](ERROR_HANDLING.md)** - Comprehensive error handling guide
- **[ERROR_HANDLING_FLOW.md](ERROR_HANDLING_FLOW.md)** - Visual error flow diagram
- **[API_EXAMPLES.md](API_EXAMPLES.md)** - API usage examples
- **Interactive API Docs** - Available at `/docs` when server is running

## Key Features Explained

### Flexible Meal Sourcing

```python
# Use database meals (default)
POST /api/diet/predict {"user_id": 1}

# Use CSV fixtures
POST /api/diet/predict {"user_id": 1, "use_csv": true}

# Override with explicit preference
POST /api/diet/predict {"user_id": 1, "use_csv": true, "preference": "vegan"}
```

### Dietary Preference Support

Supported preferences: `vegetarian`, `vegan`, `keto`, `paleo`, `mediterranean`, `gluten_free`, `low_sodium`, `high_protein`, `balanced`

### Daily Meal Plan Structure

```json
{
  "breakfast": {"name": "Oatmeal Bowl", "calories": 350, ...},
  "lunch": {"name": "Grilled Chicken Salad", "calories": 450, ...},
  "dinner": {"name": "Salmon with Quinoa", "calories": 550, ...},
  "snack": {"name": "Greek Yogurt", "calories": 150, ...},
  "daily_totals": {"calories": 1500, "protein": 100, "carbs": 150, "fat": 50}
}
```

## Configuration

Environment variables (create `.env` file):

```env
DATABASE_URL=sqlite:///./diet.db
LOG_LEVEL=INFO
MODEL_PATH=data/models/diet_model.joblib
MEAL_CSV_PATH=data/fixtures/healthy_meal_plans.csv
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Author

**Deepak Sharma**  
Email: sharmadeep5212@gmail.com

Developed as an AI-powered nutrition and diet recommendation system.

---
