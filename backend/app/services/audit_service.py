import uuid
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.app.models.audit import AuditEvent
from backend.app.core.logging import logger


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def record_event(
        self,
        event_type: str,
        actor: str = "user",
        entity_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        event = AuditEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            actor=actor,
            entity_id=entity_id,
            payload_json=payload or {}
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        logger.debug(f"Audit event recorded: {event_type} on {entity_id}")
        return event

    def list_events(self, limit: int = 100) -> List[AuditEvent]:
        stmt = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())

