from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user, require_roles
from app.models.models import EngineeringChange, User
from app.schemas.schemas import ChangeCreate, ChangeUpdate, ChangeResponse, PaginatedResponse
from app.services.services import ChangeService

router = APIRouter(prefix="/changes", tags=["Module 8: Engineering Change Management"])


def _to_response(item: EngineeringChange) -> ChangeResponse:
    resp = ChangeResponse.model_validate(item)
    resp.program_code = item.program.code if item.program else None
    resp.part_number = item.part.part_number if item.part else None
    resp.issue_code = item.issue.issue_code if item.issue else None
    return resp


@router.get("", response_model=PaginatedResponse[ChangeResponse])
def list_changes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    program_id: Optional[int] = None,
    part_id: Optional[int] = None,
    approval_status: Optional[str] = None,
    change_type: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|change_code|cost_impact_rmb|weight_impact_kg)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    service = ChangeService(db)
    items, total = service.list_changes(
        search=search,
        program_id=program_id,
        part_id=part_id,
        approval_status=approval_status,
        change_type=change_type,
        sort_by=sort_by,
        sort_order=sort_order,
        offset=(page - 1) * page_size,
        limit=page_size
    )
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaginatedResponse(
        items=[_to_response(x) for x in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/{change_id}", response_model=ChangeResponse)
def get_change(change_id: int, db: Session = Depends(get_db)):
    ecr = ChangeService(db).get_change(change_id)
    return _to_response(ecr)


@router.post("", response_model=ChangeResponse, status_code=status.HTTP_201_CREATED)
def create_change(
    payload: ChangeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "quality_lead", "design_engineer"))
):
    ecr = ChangeService(db).create_change(payload)
    return _to_response(ecr)


@router.put("/{change_id}", response_model=ChangeResponse)
def update_change(
    change_id: int,
    payload: ChangeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "quality_lead", "design_engineer"))
):
    # Enforce vertical separation of duty: Only Quality Lead or Admin can approve or implement an ECR
    if payload.approval_status in ("Approved", "Implemented") and current_user.role not in ("admin", "quality_lead"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation forbidden. Only Quality Lead or Admin can set change status to '{payload.approval_status}'. Your role is '{current_user.role}'."
        )

    ecr = ChangeService(db).update_change(change_id, payload)
    return _to_response(ecr)


@router.delete("/{change_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_change(
    change_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "quality_lead"))
):
    ChangeService(db).delete_change(change_id)
    return None
