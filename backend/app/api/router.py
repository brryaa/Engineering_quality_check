from fastapi import APIRouter
from app.api import (
    auth, programs, parts, dfmea, dvpr, tests,
    issues, root_cause, changes, dashboard, knowledge,
    traceability
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(programs.router)
api_router.include_router(parts.router)
api_router.include_router(dfmea.router)
api_router.include_router(dvpr.router)
api_router.include_router(tests.router)
api_router.include_router(issues.router)
api_router.include_router(root_cause.router)
api_router.include_router(changes.router)
api_router.include_router(dashboard.router)
api_router.include_router(knowledge.router)
api_router.include_router(traceability.router)
