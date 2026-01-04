# Error Handling Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Request                          │
│                    (POST /api/diet/predict)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Middleware                         │
│                    (Request Logging)                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Pydantic Validation                         │
│              (Validate request body schema)                     │
└────────────────┬────────────────────────────┬───────────────────┘
                 │                            │
         Valid   │                            │ Invalid
                 ▼                            ▼
┌────────────────────────────┐  ┌────────────────────────────────┐
│   API Endpoint Handler     │  │ validation_exception_handler   │
│   (api/train.py::predict)  │  │   Returns 422 with details     │
└────────┬───────────────────┘  └────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                         │
│         (Check user_id, load model, validate data)              │
└──┬──────────┬─────────────┬──────────────┬────────────────┬────┘
   │          │             │              │                │
   │ User     │ Model       │ DB           │ Validation     │ Success
   │ Missing  │ Not Trained │ Error        │ Failed         │
   ▼          ▼             ▼              ▼                ▼
┌──────┐  ┌────────────┐ ┌───────────┐ ┌─────────────┐  ┌──────┐
│ Not  │  │  Model     │ │ Database  │ │ Validation  │  │Return│
│Found │  │NotTrained  │ │   Error   │ │   Error     │  │ 200  │
│Error │  │   Error    │ │           │ │             │  │      │
└──┬───┘  └─────┬──────┘ └─────┬─────┘ └──────┬──────┘  └──────┘
   │            │              │               │
   ▼            ▼              ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│              Registered Exception Handlers                      │
│                 (core/error_handlers.py)                        │
├─────────────────────────────────────────────────────────────────┤
│  app_exception_handler                                          │
│  ├─ NotFoundError        → 404 JSON response                    │
│  ├─ ValidationError      → 400 JSON response                    │
│  ├─ ModelNotTrainedError → 503 JSON response                    │
│  ├─ DatabaseError        → 500 JSON response                    │
│  └─ InsufficientDataError → 400 JSON response                   │
│                                                                 │
│  sqlalchemy_exception_handler                                   │
│  └─ SQLAlchemyError      → 500 JSON response (sanitized)        │
│                                                                 │
│  generic_exception_handler                                      │
│  └─ Any Exception        → 500 JSON response (generic)          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Logger (core/logger.py)                      │
│              Log error with full context & stack trace          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      JSON Response to Client                    │
├─────────────────────────────────────────────────────────────────┤
│  {                                                              │
│    "error": {                                                   │
│      "message": "User with id '123' not found",                 │
│      "status_code": 404,                                        │
│      "details": {                                               │
│        "resource": "User",                                      │
│        "id": 123                                                │
│      }                                                           │
│    }                                                             │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Exception Classes (core/exceptions.py)
- Domain-specific exceptions with typed attributes
- Inherit from base `AppException` class
- Include status codes and contextual details

### 2. Exception Handlers (core/error_handlers.py)
- Convert exceptions to standardized JSON responses
- Log errors with appropriate severity levels
- Sanitize internal errors for security

### 3. API Integration
- Endpoints raise domain exceptions instead of HTTPException
- Business logic validates and raises specific errors
- Exceptions propagate through call stack to handlers

### 4. Response Format
- Consistent JSON structure for all errors
- Human-readable messages with actionable guidance
- Additional details for debugging (when safe)

## Error Flow Example

```python
# 1. Client sends request
POST /api/diet/predict
{
  "user_id": 99999
}

# 2. API endpoint tries to fetch user
user = db.get(models.User, 99999)
if not user:
    raise NotFoundError("User", 99999)  # Raises custom exception

# 3. Exception handler catches it
@app.exception_handler(AppException)
async def app_exception_handler(request, exc):
    return create_error_response(
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details
    )

# 4. Client receives formatted response
{
  "error": {
    "message": "User with id '99999' not found",
    "status_code": 404,
    "details": {
      "resource": "User",
      "id": 99999
    }
  }
}
```

## Benefits

✅ **Consistent** - All errors use same format
✅ **Debuggable** - Full logging with context
✅ **Secure** - Internal details not exposed
✅ **User-friendly** - Clear, actionable messages
✅ **Maintainable** - Centralized logic
✅ **Type-safe** - Strongly typed exceptions
