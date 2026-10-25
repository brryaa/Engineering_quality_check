from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.schemas import DVPRCreate, DVPRUpdate, DVPRResponse, PaginatedResponse
from app.services.services import DVPRService

router = APIRouter(prefix="/dvpr", tags=["Module 4: DVP&R Verification Plan"])

@router.get("", response_model=PaginatedResponse[DVPRResponse])
def list_dvprs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    program_id: Optional[int] = None,
    part_id: Optional[int] = None,
    test_phase: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|plan_code|planned_start_date|planned_end_date)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    service = DVPRService(db)
    items, total = service.list_dvprs(
        search=search, program_id=program_id, part_id=part_id,
        test_phase=test_phase, status=status,
        sort_by=sort_by, sort_order=sort_order,
        offset=(page - 1) * page_size, limit=page_size
    )
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    results = []
    for item in items:
        resp = DVPRResponse.model_validate(item)
        resp.program_code = item.program.code if item.program else None
        resp.part_number = item.part.part_number if item.part else None
        resp.test_runs_count = len(item.test_runs) if item.test_runs else 0
        results.append(resp)

    return PaginatedResponse(items=results, total=total, page=page, page_size=page_size, pages=pages)

@router.get("/{dvpr_id}", response_model=DVPRResponse)
def get_dvpr(dvpr_id: int, db: Session = Depends(get_db)):
    item = DVPRService(db).get_dvpr(dvpr_id)
    resp = DVPRResponse.model_validate(item)
    resp.program_code = item.program.code if item.program else None
    resp.part_number = item.part.part_number if item.part else None
    resp.test_runs_count = len(item.test_runs) if item.test_runs else 0
    return resp

@router.post("", response_model=DVPRResponse, status_code=status.HTTP_201_CREATED)
def create_dvpr(payload: DVPRCreate, db: Session = Depends(get_db)):
    dvpr = DVPRService(db).create_dvpr(payload)
    resp = DVPRResponse.model_validate(dvpr)
    resp.program_code = dvpr.program.code if dvpr.program else None
    resp.part_number = dvpr.part.part_number if dvpr.part else None
    resp.test_runs_count = 0
    return resp

@router.put("/{dvpr_id}", response_model=DVPRResponse)
def update_dvpr(dvpr_id: int, payload: DVPRUpdate, db: Session = Depends(get_db)):
    dvpr = DVPRService(db).update_dvpr(dvpr_id, payload)
    resp = DVPRResponse.model_validate(dvpr)
    resp.program_code = dvpr.program.code if dvpr.program else None
    resp.part_number = dvpr.part.part_number if dvpr.part else None
    resp.test_runs_count = len(dvpr.test_runs) if dvpr.test_runs else 0
    return resp

@router.delete("/{dvpr_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dvpr(dvpr_id: int, db: Session = Depends(get_db)):
    DVPRService(db).delete_dvpr(dvpr_id)
    return None
