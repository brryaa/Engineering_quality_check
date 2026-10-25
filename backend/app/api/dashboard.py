from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.schemas import QualityDashboardStats
from app.services.services import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Module 9: R&D Quality Statistics Dashboard"])


@router.get("/stats", response_model=QualityDashboardStats)
def get_dashboard_stats(
    program_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    return DashboardService(db).get_stats(program_id=program_id)
