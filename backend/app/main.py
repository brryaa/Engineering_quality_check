from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError, IntegrityError
from sqlalchemy.orm.exc import StaleDataError
from app.core.config import settings
from app.core.exceptions import (
    app_exception_handler,
    generic_exception_handler,
    stale_data_exception_handler,
    db_operational_exception_handler,
    db_integrity_exception_handler
)
from app.api.router import api_router
from app.core.logging import logger

from app.core.security_middleware import SecurityMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Automotive Closures & Sealing Engineering Quality Management Platform (EQL)"
)

# Security & CORS middlewares
app.add_middleware(SecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(HTTPException, app_exception_handler)
app.add_exception_handler(StaleDataError, stale_data_exception_handler)
app.add_exception_handler(OperationalError, db_operational_exception_handler)
app.add_exception_handler(IntegrityError, db_integrity_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION
    }
