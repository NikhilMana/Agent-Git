import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base, utc_now


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)  # commit, restore, branch_create, merge, override, ingest, retrieve
    actor: Mapped[str] = mapped_column(String(64), default="user", nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    payload_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

