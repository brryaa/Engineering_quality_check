from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user, require_roles
from app.models.models import User
from app.schemas.schemas import PartCreate, PartUpdate, PartResponse, PaginatedResponse
from app.services.services import PartService

router = APIRouter(prefix="/parts", tags=["Module 2: Parts & Subsystems"])

@router.get("", response_model=PaginatedResponse[PartResponse])
def list_parts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    program_id: Optional[int] = None,
    subsystem: Optional[str] = None,
    category: Optional[str] = None,
    safety_critical: Optional[bool] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|part_number|name|weight_kg)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    service = PartService(db)
    items, total = service.list_parts(
        search=search, program_id=program_id, subsystem=subsystem,
        category=category, safety_critical=safety_critical,
        sort_by=sort_by, sort_order=sort_order,
        offset=(page - 1) * page_size, limit=page_size
    )
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    results = []
    for p in items:
        resp = PartResponse.model_validate(p)
        resp.program_code = p.program.code if p.program else None
        results.append(resp)

    return PaginatedResponse(items=results, total=total, page=page, page_size=page_size, pages=pages)

@router.get("/{part_id}", response_model=PartResponse)
def get_part(part_id: int, db: Session = Depends(get_db)):
    p = PartService(db).get_part(part_id)
    resp = PartResponse.model_validate(p)
    resp.program_code = p.program.code if p.program else None
    return resp

@router.post("", response_model=PartResponse, status_code=status.HTTP_201_CREATED)
def create_part(
    payload: PartCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "quality_lead", "design_engineer"))
):
    part = PartService(db).create_part(payload)
    resp = PartResponse.model_validate(part)
    resp.program_code = part.program.code if part.program else None
    return resp

@router.put("/{part_id}", response_model=PartResponse)
def update_part(
    part_id: int,
    payload: PartUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "quality_lead", "design_engineer"))
):
    part = PartService(db).update_part(part_id, payload)
    resp = PartResponse.model_validate(part)
    resp.program_code = part.program.code if part.program else None
    return resp

@router.delete("/{part_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_part(
    part_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "quality_lead"))
):
    PartService(db).delete_part(part_id)
    return None
