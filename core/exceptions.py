"""Custom exception classes for the application.

Defines domain-specific exceptions that can be raised throughout the
application and handled consistently by exception handlers.
"""

from typing import Optional, Any, Dict


class AppException(Exception):
    """Base exception class for all application exceptions.
    
    Attributes:
        message: Human-readable error message.
        status_code: HTTP status code to return.
        details: Optional additional error details.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize application exception.
        
        Args:
            message: Error message.
            status_code: HTTP status code (default: 500).
            details: Optional dictionary with additional error context.
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, resource: str, identifier: Any):
        """Initialize not found error.
        
        Args:
            resource: Type of resource (e.g., 'User', 'Meal').
            identifier: ID or identifier that was not found.
        """
        message = f"{resource} with id '{identifier}' not found"
        super().__init__(message, status_code=404, details={"resource": resource, "id": identifier})


class ValidationError(AppException):
    """Exception raised when input validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        """Initialize validation error.
        
        Args:
            message: Validation error message.
            field: Optional field name that failed validation.
        """
        details = {"field": field} if field else {}
        super().__init__(message, status_code=400, details=details)


class DatabaseError(AppException):
    """Exception raised when database operations fail."""

    def __init__(self, message: str, operation: Optional[str] = None):
        """Initialize database error.
        
        Args:
            message: Database error message.
            operation: Optional operation that failed (e.g., 'create', 'update').
        """
        details = {"operation": operation} if operation else {}
        super().__init__(message, status_code=500, details=details)


class ModelNotTrainedError(AppException):
    """Exception raised when attempting to use an untrained ML model."""

    def __init__(self):
        """Initialize model not trained error."""
        super().__init__(
            "Model not trained. Please train the model first using /api/diet/train endpoint.",
            status_code=503,
            details={"train_endpoint": "/api/diet/train"}
        )


class InsufficientDataError(AppException):
    """Exception raised when insufficient data is available for an operation."""

    def __init__(self, message: str, minimum_required: Optional[int] = None):
        """Initialize insufficient data error.
        
        Args:
            message: Error message.
            minimum_required: Optional minimum number of records required.
        """
        details = {"minimum_required": minimum_required} if minimum_required else {}
        super().__init__(message, status_code=400, details=details)


class ConfigurationError(AppException):
    """Exception raised when application configuration is invalid."""

    def __init__(self, message: str, config_key: Optional[str] = None):
        """Initialize configuration error.
        
        Args:
            message: Configuration error message.
            config_key: Optional configuration key that is invalid.
        """
        details = {"config_key": config_key} if config_key else {}
        super().__init__(message, status_code=500, details=details)
