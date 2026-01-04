"""Error handlers for FastAPI application.

Provides consistent error response formatting and exception handling
across all API endpoints.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from core.exceptions import AppException
from core.logger import get_logger
from typing import Union
import traceback

logger = get_logger("core.error_handlers")


def create_error_response(
    message: str,
    status_code: int = 500,
    details: dict = None,
    request_id: str = None
) -> JSONResponse:
    """Create a standardized error response.
    
    Args:
        message: Error message.
        status_code: HTTP status code.
        details: Optional error details dictionary.
        request_id: Optional request ID for tracking.
        
    Returns:
        JSONResponse with error details.
    """
    error_body = {
        "error": {
            "message": message,
            "status_code": status_code,
        }
    }
    
    if details:
        error_body["error"]["details"] = details
    
    if request_id:
        error_body["error"]["request_id"] = request_id
    
    return JSONResponse(
        status_code=status_code,
        content=error_body
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions.
    
    Args:
        request: FastAPI request object.
        exc: Application exception instance.
        
    Returns:
        JSONResponse with error details.
    """
    logger.warning(
        "Application error: %s [%s %s]",
        exc.message,
        request.method,
        request.url.path
    )
    
    return create_error_response(
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors.
    
    Args:
        request: FastAPI request object.
        exc: Pydantic validation error.
        
    Returns:
        JSONResponse with validation error details.
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        "Validation error on %s %s: %s",
        request.method,
        request.url.path,
        errors
    )
    
    return create_error_response(
        message="Validation error",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": errors}
    )


async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy database errors.
    
    Args:
        request: FastAPI request object.
        exc: SQLAlchemy error.
        
    Returns:
        JSONResponse with database error details.
    """
    logger.error(
        "Database error on %s %s: %s",
        request.method,
        request.url.path,
        str(exc),
        exc_info=True
    )
    
    # Don't expose internal database errors to clients
    return create_error_response(
        message="A database error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"type": "database_error"}
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle all unhandled exceptions.
    
    Args:
        request: FastAPI request object.
        exc: Unhandled exception.
        
    Returns:
        JSONResponse with generic error message.
    """
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        str(exc),
        exc_info=True
    )
    
    # Log full traceback for debugging
    logger.error("Traceback: %s", traceback.format_exc())
    
    # Return generic error to client
    return create_error_response(
        message="An internal server error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"type": "internal_error"}
    )


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app.
    
    Args:
        app: FastAPI application instance.
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered")
