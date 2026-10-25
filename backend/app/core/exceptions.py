import uuid
from typing import Any
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, IntegrityError
from sqlalchemy.orm.exc import StaleDataError
from app.core.logging import logger


class EntityNotFoundError(HTTPException):
    def __init__(self, entity_name: str, entity_id: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} with id/code '{entity_id}' not found."
        )


class BusinessRuleViolationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Business rule violation: {detail}"
        )


class DuplicateEntityError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class ConcurrencyConflictError(HTTPException):
    def __init__(self, detail: str = "Resource was modified by another transaction. Please reload."):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


async def app_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTPException [{exc.status_code}] on {request.method} {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail, "status_code": exc.status_code}
    )


async def stale_data_exception_handler(request: Request, exc: StaleDataError):
    logger.warning(f"Optimistic lock conflict on {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "success": False,
            "error": "Conflict: This record was modified by another user. Please refresh and retry.",
            "status_code": 409
        }
    )


async def db_operational_exception_handler(request: Request, exc: OperationalError):
    error_id = str(uuid.uuid4())[:8]
    logger.error(f"Database operational failure [ref={error_id}] on {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "error": "Database service is temporarily unavailable. Transaction aborted.",
            "reference_id": error_id,
            "status_code": 503
        }
    )


async def db_integrity_exception_handler(request: Request, exc: IntegrityError):
    error_id = str(uuid.uuid4())[:8]
    logger.error(f"Database integrity constraint violation [ref={error_id}] on {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": "Database constraint violation (e.g. invalid foreign key or duplicate key).",
            "reference_id": error_id,
            "status_code": 400
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    error_id = str(uuid.uuid4())[:8]
    logger.error(f"Unhandled server error [ref={error_id}] on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error occurred.",
            "reference_id": error_id,
            "status_code": 500
        }
    )
