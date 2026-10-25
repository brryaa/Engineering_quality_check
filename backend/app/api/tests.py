from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.schemas import TestRunCreate, TestRunUpdate, TestRunResponse, PaginatedResponse
from app.services.services import TestRunService

router = APIRouter(prefix="/tests", tags=["Module 5: Test Execution Records"])

@router.get("", response_model=PaginatedResponse[TestRunResponse])
def list_test_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    dvpr_id: Optional[int] = None,
    result: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|test_date|run_number|cycles_completed)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    service = TestRunService(db)
    items, total = service.list_test_runs(
        search=search, dvpr_id=dvpr_id, result=result,
        sort_by=sort_by, sort_order=sort_order,
        offset=(page - 1) * page_size, limit=page_size
    )
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    results = []
    for item in items:
        resp = TestRunResponse.model_validate(item)
        resp.plan_code = item.dvpr.plan_code if item.dvpr else None
        resp.test_name = item.dvpr.test_name if item.dvpr else None
        results.append(resp)

    return PaginatedResponse(items=results, total=total, page=page, page_size=page_size, pages=pages)

@router.get("/{test_id}", response_model=TestRunResponse)
def get_test_run(test_id: int, db: Session = Depends(get_db)):
    item = TestRunService(db).get_test_run(test_id)
    resp = TestRunResponse.model_validate(item)
    resp.plan_code = item.dvpr.plan_code if item.dvpr else None
    resp.test_name = item.dvpr.test_name if item.dvpr else None
    return resp

@router.post("", response_model=TestRunResponse, status_code=status.HTTP_201_CREATED)
def create_test_run(payload: TestRunCreate, db: Session = Depends(get_db)):
    test_run = TestRunService(db).create_test_run(payload)
    resp = TestRunResponse.model_validate(test_run)
    resp.plan_code = test_run.dvpr.plan_code if test_run.dvpr else None
    resp.test_name = test_run.dvpr.test_name if test_run.dvpr else None
    return resp

@router.put("/{test_id}", response_model=TestRunResponse)
def update_test_run(test_id: int, payload: TestRunUpdate, db: Session = Depends(get_db)):
    test_run = TestRunService(db).update_test_run(test_id, payload)
    resp = TestRunResponse.model_validate(test_run)
    resp.plan_code = test_run.dvpr.plan_code if test_run.dvpr else None
    resp.test_name = test_run.dvpr.test_name if test_run.dvpr else None
    return resp

@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_run(test_id: int, db: Session = Depends(get_db)):
    TestRunService(db).delete_test_run(test_id)
    return None
