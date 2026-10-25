from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.schemas import DFMEACreate, DFMEAUpdate, DFMEAResponse, PaginatedResponse
from app.services.services import DFMEAService

router = APIRouter(prefix="/dfmea", tags=["Module 3: DFMEA Risk Analysis"])

@router.get("", response_model=PaginatedResponse[DFMEAResponse])
def list_dfmea(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    part_id: Optional[int] = None,
    action_priority: Optional[str] = None,
    action_status: Optional[str] = None,
    min_rpn: Optional[int] = None,
    min_severity: Optional[int] = None,
    sort_by: str = Query("rpn", pattern="^(rpn|severity|occurrence|detection|created_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    service = DFMEAService(db)
    items, total = service.list_dfmeas(
        search=search, part_id=part_id,
        action_priority=action_priority, action_status=action_status,
        min_rpn=min_rpn, min_severity=min_severity,
        sort_by=sort_by, sort_order=sort_order,
        offset=(page - 1) * page_size, limit=page_size
    )
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    results = []
    for item in items:
        resp = DFMEAResponse.model_validate(item)
        resp.part_number = item.part.part_number if item.part else None
        results.append(resp)

    return PaginatedResponse(items=results, total=total, page=page, page_size=page_size, pages=pages)

@router.get("/{dfmea_id}", response_model=DFMEAResponse)
def get_dfmea(dfmea_id: int, db: Session = Depends(get_db)):
    item = DFMEAService(db).get_dfmea(dfmea_id)
    resp = DFMEAResponse.model_validate(item)
    resp.part_number = item.part.part_number if item.part else None
    return resp

@router.post("", response_model=DFMEAResponse, status_code=status.HTTP_201_CREATED)
def create_dfmea(payload: DFMEACreate, db: Session = Depends(get_db)):
    dfmea = DFMEAService(db).create_dfmea(payload)
    resp = DFMEAResponse.model_validate(dfmea)
    resp.part_number = dfmea.part.part_number if dfmea.part else None
    return resp

@router.put("/{dfmea_id}", response_model=DFMEAResponse)
def update_dfmea(dfmea_id: int, payload: DFMEAUpdate, db: Session = Depends(get_db)):
    dfmea = DFMEAService(db).update_dfmea(dfmea_id, payload)
    resp = DFMEAResponse.model_validate(dfmea)
    resp.part_number = dfmea.part.part_number if dfmea.part else None
    return resp

@router.delete("/{dfmea_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dfmea(dfmea_id: int, db: Session = Depends(get_db)):
    DFMEAService(db).delete_dfmea(dfmea_id)
    return None
