# Error Handling Implementation

This document describes the comprehensive error handling system implemented for the AI-Powered Dietitian Service API.

## Overview

The error handling system provides consistent, user-friendly error responses across all API endpoints using custom exception classes and centralized exception handlers.

## Architecture

### 1. Custom Exception Classes (`core/exceptions.py`)

Seven custom exception classes extending a base `AppException`:

- **AppException** - Base exception with status_code, message, and details
- **NotFoundError** (404) - Resource not found
- **ValidationError** (400) - Input validation failed
- **DatabaseError** (500) - Database operation failed
- **ModelNotTrainedError** (503) - ML model not trained
- **InsufficientDataError** (400) - Insufficient data for operation
- **ConfigurationError** (500) - Invalid configuration

### 2. Exception Handlers (`core/error_handlers.py`)

Centralized handlers that convert exceptions to standardized JSON responses:

```python
{
    "error": {
        "message": "User with id '123' not found",
        "status_code": 404,
        "details": {
            "resource": "User",
            "id": 123
        }
    }
}
```

Handlers registered in `main.py`:
- `app_exception_handler` - Handles custom AppException subclasses
- `validation_exception_handler` - Handles Pydantic validation errors
- `sqlalchemy_exception_handler` - Handles database errors
- `generic_exception_handler` - Catches all unhandled exceptions

### 3. API Integration

All API endpoints updated to use custom exceptions:

#### api/users.py
- `InsufficientDataError` when no meals available
- Proper docstring documentation of raised exceptions

#### api/recommendations.py
- `NotFoundError` for non-existent users/meals
- Validation before processing feedback

#### api/train.py
- `ValidationError` when neither user_id nor profile provided
- `NotFoundError` for non-existent user_id
- `ModelNotTrainedError` propagated from service layer
- Exception re-raising preserves custom exceptions

#### services/diet_trainer.py
- `ModelNotTrainedError` when model not trained
- Clear guidance in error message

#### main.py
- `DatabaseError` for health check failures
- Exception handlers registered on app startup

## Error Response Format

All errors follow a consistent JSON structure:

```json
{
    "error": {
        "message": "Human-readable error message",
        "status_code": 400,
        "details": {
            "key": "additional context"
        }
    }
}
```

### HTTP Status Codes

- **400** - Bad Request (validation, insufficient data)
- **404** - Not Found (resource doesn't exist)
- **422** - Unprocessable Entity (Pydantic validation)
- **500** - Internal Server Error (database, configuration)
- **503** - Service Unavailable (model not trained)

## Testing

Comprehensive test suite in `tests/test_error_handling.py`:

1. **test_user_not_found_raises_404** - Verifies NotFoundError for missing users
2. **test_meal_not_found_raises_404** - Verifies NotFoundError for missing meals
3. **test_predict_without_params_raises_validation_error** - Validates required parameters
4. **test_exception_classes_have_proper_attributes** - Tests exception construction

All 12 tests passing (8 original + 4 new error handling tests).

## Benefits

1. **Consistency** - All errors follow same response format
2. **Debuggability** - Detailed logging with full context
3. **Security** - Internal errors don't expose sensitive information
4. **User Experience** - Clear, actionable error messages
5. **Maintainability** - Centralized error handling logic
6. **Type Safety** - Strongly typed exception classes with proper docstrings

## Usage Examples

### Raising Custom Exceptions

```python
# Not found error
raise NotFoundError("User", user_id)

# Validation error
raise ValidationError("Either user_id or profile must be provided")

# Insufficient data
raise InsufficientDataError("No meals available in database")

# Model not trained
raise ModelNotTrainedError()
```

### Exception Handler Output

```python
# NotFoundError("User", 123) produces:
{
    "error": {
        "message": "User with id '123' not found",
        "status_code": 404,
        "details": {
            "resource": "User",
            "id": 123
        }
    }
}

# ModelNotTrainedError() produces:
{
    "error": {
        "message": "Model not trained. Please train the model first using /api/diet/train endpoint.",
        "status_code": 503,
        "details": {
            "train_endpoint": "/api/diet/train"
        }
    }
}
```

## Logging

All errors are logged with appropriate severity levels:

- **WARNING** - Application errors (NotFoundError, ValidationError)
- **ERROR** - System errors (DatabaseError, unhandled exceptions)
- **INFO** - Exception handler registration

Full stack traces captured for debugging while sanitizing responses sent to clients.

## Future Enhancements

Potential improvements for consideration:

1. Request ID tracking for distributed tracing
2. Rate limiting with custom exceptions
3. Internationalization (i18n) for error messages
4. Error analytics and monitoring integration
5. OpenAPI schema documentation for error responses
