# API Request & Response Examples

## 1. Create User with Meal Plan

**Endpoint:** `POST /api/create-user-with-plan`

### Request Body Example:
```json
{
  "name": "John Doe",
  "age": 30,
  "height": 175.0,
  "weight": 75.0,
  "gender": "male",
  "activity_level": "moderately_active",
  "dietary_preference": "balanced",
  "health_goal": "maintain",
  "allergies": ["peanuts", "shellfish"]
}
```

### Field Options:
- **name**: Any string (required)
- **age**: 18-100 (required)
- **height**: 100-250 cm (required)
- **weight**: 30-300 kg (required)
- **gender**: `"male"` | `"female"`
- **activity_level**: 
  - `"sedentary"`
  - `"lightly_active"`
  - `"moderately_active"`
  - `"very_active"`
  - `"extremely_active"`
- **dietary_preference**:
  - `"balanced"`
  - `"keto"`
  - `"low_carb"`
  - `"high-protein"`
  - `"vegetarian"`
  - `"vegan"`
  - `"paleo"`
  - `"mediterranean"`
  - `"gluten_free"`
- **health_goal**:
  - `"weight_loss"`
  - `"muscle_gain"`
  - `"maintain"`
- **allergies**: Array of strings (optional)

### Response Example:
```json
{
  "user_id": 1,
  "name": "John Doe",
  "age": 30,
  "height": 175.0,
  "weight": 75.0,
  "bmi": 24.5,
  "health_goal": "maintain",
  "dietary_preference": "balanced",
  "target_calories": 2633,
  "target_macros": {
    "protein": 197,
    "carbs": 263,
    "fat": 88
  },
  "meal_plan": {
    "date": "2026-01-04",
    "breakfast": {
      "id": 1,
      "name": "Oatmeal with Berries",
      "meal_type": "breakfast",
      "calories": 350.0,
      "protein": 12.0,
      "carbs": 54.0,
      "fat": 8.0,
      "ingredients": ["oats", "blueberries", "strawberries", "honey"]
    },
    "lunch": {
      "id": 5,
      "name": "Grilled Chicken Salad",
      "meal_type": "lunch",
      "calories": 450.0,
      "protein": 35.0,
      "carbs": 25.0,
      "fat": 22.0,
      "ingredients": ["chicken breast", "mixed greens", "cherry tomatoes", "olive oil"]
    },
    "dinner": {
      "id": 10,
      "name": "Salmon with Quinoa",
      "meal_type": "dinner",
      "calories": 520.0,
      "protein": 40.0,
      "carbs": 45.0,
      "fat": 18.0,
      "ingredients": ["salmon fillet", "quinoa", "broccoli", "lemon"]
    },
    "snack": {
      "id": 15,
      "name": "Greek Yogurt",
      "meal_type": "snack",
      "calories": 150.0,
      "protein": 15.0,
      "carbs": 12.0,
      "fat": 5.0,
      "ingredients": ["greek yogurt", "honey"]
    },
    "daily_totals": {
      "calories": 1470.0,
      "protein": 102.0,
      "carbs": 136.0,
      "fat": 53.0
    }
  },
  "created_at": "2026-01-04T10:30:00.000000"
}
```

---

## 2. Predict Diet Recommendation

**Endpoint:** `POST /api/diet/predict`

### Request Body Example (with profile):
```json
{
  "profile": {
    "name": "Jane Smith",
    "Age": 28,
    "Gender": "Female",
    "Weight_kg": 65.0,
    "Height_cm": 165.0,
    "Physical_Activity_Level": "lightly_active",
    "health_goal": "weight_loss"
  },
  "use_csv": true,
  "preference": "vegan"
}
```

### Request Body Example (with user_id):
```json
{
  "user_id": 1,
  "use_csv": false,
  "preference": "keto"
}
```

### Field Options:
- **user_id**: Integer (use existing user from database)
- **profile**: Object with user attributes (alternative to user_id)
  - **name**: String (optional, defaults to "Guest User")
  - **Age**: Integer (default: 30)
  - **Gender**: `"Male"` | `"Female"` (default: "male")
  - **Weight_kg**: Float (default: 70.0)
  - **Height_cm**: Float (default: 170.0)
  - **Physical_Activity_Level**: 
    - `"Sedentary"`
    - `"Light"`
    - `"Moderate"`
    - `"Active"`
    - `"Very Active"`
  - **health_goal**: `"weight_loss"` | `"muscle_gain"` | `"maintain"` (default: "maintain")
- **use_csv**: Boolean (if true, meals sourced from CSV instead of DB)
- **preference**: String (explicit dietary preference override)
  - `"veg"` | `"vegetarian"`
  - `"vegan"`
  - `"keto"` | `"low_carb"`
  - `"gluten_free"`
  - `"paleo"`
  - `"mediterranean"`
  - `"balanced"`

### Response Example:
```json
{
  "user_id": null,
  "name": "Jane Smith",
  "age": 28,
  "height": 165.0,
  "weight": 65.0,
  "bmi": 23.9,
  "gender": "Female",
  "activity_level": "lightly_active",
  "health_goal": "weight_loss",
  "dietary_preference": "low_carb",
  "target_calories": 1706,
  "target_macros": {
    "protein": 128,
    "carbs": 171,
    "fat": 57
  },
  "diet_recommendation": "Low_Carb",
  "confidence": 0.52,
  "probabilities": {
    "Balanced": 0.31,
    "Low_Carb": 0.52,
    "Low_Sodium": 0.17
  },
  "recommended_meals": [
    {
      "id": null,
      "name": "Grilled Salmon",
      "meal_type": "dinner",
      "calories": 350.0,
      "protein": 42.0,
      "carbs": 5.0,
      "fat": 18.0,
      "ingredients": ["salmon", "olive oil", "lemon", "herbs"],
      "verified": true
    },
    {
      "id": null,
      "name": "Almond Flour Pancakes",
      "meal_type": "breakfast",
      "calories": 280.0,
      "protein": 12.0,
      "carbs": 15.0,
      "fat": 20.0,
      "ingredients": ["almond flour", "eggs", "coconut oil"],
      "verified": true
    }
  ],
  "daily_plan": {
    "date": "2026-01-04",
    "breakfast": {
      "id": null,
      "name": "Almond Flour Pancakes",
      "meal_type": "breakfast",
      "calories": 280.0,
      "protein": 12.0,
      "carbs": 15.0,
      "fat": 20.0,
      "ingredients": ["almond flour", "eggs", "coconut oil"]
    },
    "lunch": {
      "id": null,
      "name": "Turkey Lettuce Wraps",
      "meal_type": "lunch",
      "calories": 320.0,
      "protein": 35.0,
      "carbs": 8.0,
      "fat": 16.0,
      "ingredients": ["turkey breast", "lettuce", "avocado", "tomato"]
    },
    "dinner": {
      "id": null,
      "name": "Grilled Salmon",
      "meal_type": "dinner",
      "calories": 350.0,
      "protein": 42.0,
      "carbs": 5.0,
      "fat": 18.0,
      "ingredients": ["salmon", "olive oil", "lemon", "herbs"]
    },
    "daily_totals": {
      "calories": 950.0,
      "protein": 89.0,
      "carbs": 28.0,
      "fat": 54.0
    }
  }
}
```

---

## 3. Train Diet Model

**Endpoint:** `POST /api/diet/train`

### Request Body Example:
```json
{
  "csv_path": "/path/to/diet_dataset.csv"
}
```

### Response Example:
```json
{
  "model_path": "/path/to/models/diet_model.joblib",
  "accuracy": 0.87,
  "classes": ["Balanced", "Low_Carb", "Low_Sodium", "High_Protein", "Gluten_Free"]
}
```

---

## 4. Get All Meals

**Endpoint:** `GET /api/meals`

### Response Example:
```json
[
  {
    "id": 1,
    "name": "Oatmeal with Berries",
    "meal_type": "breakfast",
    "calories": 350.0,
    "protein": 12.0,
    "carbs": 54.0,
    "fat": 8.0,
    "ingredients": ["oats", "blueberries", "strawberries", "honey"]
  },
  {
    "id": 2,
    "name": "Greek Yogurt Bowl",
    "meal_type": "breakfast",
    "calories": 220.0,
    "protein": 18.0,
    "carbs": 25.0,
    "fat": 6.0,
    "ingredients": ["greek yogurt", "granola", "mixed berries"]
  }
]
```

---

## 5. Submit Feedback

**Endpoint:** `POST /api/recommendations/{plan_id}/feedback`

### Request Body Example:
```json
{
  "user_id": 1,
  "plan_id": 5,
  "meal_id": 10,
  "rating": 5
}
```

### Field Options:
- **rating**: 1-5 (required)

### Response Example:
```json
{
  "id": 1,
  "user_id": 1,
  "plan_id": 5,
  "meal_id": 10,
  "rating": 5,
  "created_at": "2026-01-04T10:30:00.000000"
}
```

---

## 6. Get Similar Meals

**Endpoint:** `GET /api/recommendations/meal/{meal_id}/similar?top_k=5`

### Response Example:
```json
[
  {
    "id": 3,
    "name": "Protein Smoothie Bowl",
    "meal_type": "breakfast",
    "calories": 280.0,
    "protein": 22.0,
    "carbs": 35.0,
    "fat": 6.0,
    "dietary_tags": ["high-protein", "vegetarian"],
    "ingredients": ["protein powder", "banana", "berries", "almond milk"],
    "score": 0.92
  },
  {
    "id": 7,
    "name": "Egg White Omelette",
    "meal_type": "breakfast",
    "calories": 200.0,
    "protein": 24.0,
    "carbs": 8.0,
    "fat": 7.0,
    "dietary_tags": ["high-protein", "low-carb"],
    "ingredients": ["egg whites", "spinach", "tomatoes", "cheese"],
    "score": 0.85
  }
]
```

---

## 7. List Users with Plans

**Endpoint:** `GET /api/users-with-plans?limit=50&skip=0`

### Response Example:
```json
{
  "total_users": 2,
  "users": [
    {
      "user_id": 1,
      "name": "John Doe",
      "age": 30,
      "height": 175.0,
      "weight": 75.0,
      "bmi": 24.5,
      "health_goal": "maintain",
      "dietary_preference": "balanced",
      "target_calories": 2633,
      "target_macros": {
        "protein": 197,
        "carbs": 263,
        "fat": 88
      },
      "meal_plan": {
        "date": "2026-01-04",
        "breakfast": { ... },
        "lunch": { ... },
        "dinner": { ... },
        "snack": { ... },
        "daily_totals": {
          "calories": 1470.0,
          "protein": 102.0,
          "carbs": 136.0,
          "fat": 53.0
        }
      },
      "created_at": "2026-01-04T10:30:00.000000"
    }
  ]
}
```
