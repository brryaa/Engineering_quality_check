from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user, require_roles
from app.models.models import User
from app.schemas.schemas import KnowledgeItemCreate, KnowledgeItemUpdate, KnowledgeItemResponse, PaginatedResponse
from app.services.services import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["Module 10: Engineering Knowledge Retrieval"])


@router.get("", response_model=PaginatedResponse[KnowledgeItemResponse])
def list_knowledge(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    subsystem: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|doc_code|title)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    items, total = service.list_knowledge(
        search=search,
        subsystem=subsystem,
        category=category,
        tag=tag,
        sort_by=sort_by,
        sort_order=sort_order,
        offset=(page - 1) * page_size,
        limit=page_size
    )
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/{kb_id}", response_model=KnowledgeItemResponse)
def get_knowledge_item(kb_id: int, db: Session = Depends(get_db)):
    return KnowledgeService(db).get_knowledge_item(kb_id)


@router.post("", response_model=KnowledgeItemResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_item(
    payload: KnowledgeItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "quality_lead", "design_engineer"))
):
    return KnowledgeService(db).create_knowledge_item(payload)


@router.put("/{kb_id}", response_model=KnowledgeItemResponse)
def update_knowledge_item(
    kb_id: int,
    payload: KnowledgeItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "quality_lead", "design_engineer"))
):
    return KnowledgeService(db).update_knowledge_item(kb_id, payload)


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_item(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    KnowledgeService(db).delete_knowledge_item(kb_id)
    return None
