from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.services.audit_service import AuditService
from backend.app.schemas.audit import AuditEventResponse

router = APIRouter(prefix="/audit", tags=["Audit Events"])


@router.get("/events", response_model=List[AuditEventResponse])
def list_audit_events(limit: int = 100, db: Session = Depends(get_db)):
    audit_svc = AuditService(db)
    return audit_svc.list_events(limit=limit)

