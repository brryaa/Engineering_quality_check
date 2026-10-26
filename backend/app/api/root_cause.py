from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user, require_roles
from app.models.models import RootCauseAnalysis, User
from app.schemas.schemas import RootCauseCreate, RootCauseUpdate, RootCauseResponse, PaginatedResponse
from app.services.services import RootCauseService

router = APIRouter(prefix="/root-cause", tags=["Module 7: Failure Root Cause Analysis"])


def _to_response(item: RootCauseAnalysis) -> RootCauseResponse:
    resp = RootCauseResponse.model_validate(item)
    resp.issue_code = item.issue.issue_code if item.issue else None
    return resp


@router.get("", response_model=PaginatedResponse[RootCauseResponse])
def list_root_causes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    issue_id: Optional[int] = None,
    analysis_method: Optional[str] = None,
    verification_result: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|analyzed_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    service = RootCauseService(db)
    items, total = service.list_root_causes(
        issue_id=issue_id,
        analysis_method=analysis_method,
        verification_result=verification_result,
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


@router.get("/{rc_id}", response_model=RootCauseResponse)
def get_root_cause(rc_id: int, db: Session = Depends(get_db)):
    rc = RootCauseService(db).get_root_cause(rc_id)
    return _to_response(rc)


@router.get("/by-issue/{issue_id}", response_model=RootCauseResponse)
def get_root_cause_by_issue(issue_id: int, db: Session = Depends(get_db)):
    rc = RootCauseService(db).get_by_issue_id(issue_id)
    return _to_response(rc)


@router.post("", response_model=RootCauseResponse, status_code=status.HTTP_201_CREATED)
def create_root_cause(
    payload: RootCauseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "quality_lead", "design_engineer"))
):
    rc = RootCauseService(db).create_root_cause(payload)
    return _to_response(rc)


@router.put("/{rc_id}", response_model=RootCauseResponse)
def update_root_cause(
    rc_id: int,
    payload: RootCauseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "quality_lead", "design_engineer"))
):
    rc = RootCauseService(db).update_root_cause(rc_id, payload)
    return _to_response(rc)


@router.delete("/{rc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_root_cause(
    rc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "quality_lead"))
):
    RootCauseService(db).delete_root_cause(rc_id)
    return None
