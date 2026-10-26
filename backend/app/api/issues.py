from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user, require_roles
from app.models.models import EngineeringIssue, User
from app.schemas.schemas import IssueCreate, IssueUpdate, IssueResponse, PaginatedResponse
from app.services.services import IssueService

router = APIRouter(prefix="/issues", tags=["Module 6: Engineering Issue Tracking"])


def _to_response(item: EngineeringIssue) -> IssueResponse:
    resp = IssueResponse.model_validate(item)
    resp.program_code = item.program.code if item.program else None
    resp.part_number = item.part.part_number if item.part else None
    resp.has_root_cause = item.root_cause is not None
    return resp


@router.get("", response_model=PaginatedResponse[IssueResponse])
def list_issues(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    program_id: Optional[int] = None,
    part_id: Optional[int] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|due_date|severity|status)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    service = IssueService(db)
    items, total = service.list_issues(
        search=search,
        program_id=program_id,
        part_id=part_id,
        severity=severity,
        status=status,
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


@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = IssueService(db).get_issue(issue_id)
    return _to_response(issue)


@router.post("", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_issue(
    payload: IssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "quality_lead", "design_engineer"))
):
    issue = IssueService(db).create_issue(payload)
    return _to_response(issue)


@router.put("/{issue_id}", response_model=IssueResponse)
def update_issue(
    issue_id: int,
    payload: IssueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "quality_lead", "design_engineer"))
):
    issue = IssueService(db).update_issue(issue_id, payload)
    return _to_response(issue)


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "quality_lead"))
):
    IssueService(db).delete_issue(issue_id)
    return None
