from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.schemas import ProgramCreate, ProgramUpdate, ProgramResponse, PaginatedResponse
from app.services.services import ProgramService

router = APIRouter(prefix="/programs", tags=["Module 1: Programs & Vehicle Models"])

@router.get("", response_model=PaginatedResponse[ProgramResponse])
def list_programs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    phase: Optional[str] = None,
    platform: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|code|name|sop_date)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    service = ProgramService(db)
    items, total = service.list_programs(
        search=search, phase=phase, platform=platform,
        sort_by=sort_by, sort_order=sort_order,
        offset=(page - 1) * page_size, limit=page_size
    )
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)

@router.get("/{program_id}", response_model=ProgramResponse)
def get_program(program_id: int, db: Session = Depends(get_db)):
    return ProgramService(db).get_program(program_id)

@router.post("", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
def create_program(payload: ProgramCreate, db: Session = Depends(get_db)):
    return ProgramService(db).create_program(payload)

@router.put("/{program_id}", response_model=ProgramResponse)
def update_program(program_id: int, payload: ProgramUpdate, db: Session = Depends(get_db)):
    return ProgramService(db).update_program(program_id, payload)

@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_program(program_id: int, db: Session = Depends(get_db)):
    ProgramService(db).delete_program(program_id)
    return None
