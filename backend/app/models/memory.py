import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base, utc_now


class MemoryItem(Base):
    __tablename__ = "memory_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True)
    logical_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)  # fact | preference | decision | constraint | task | summary | other
    retention_action: Mapped[str] = mapped_column(String(32), nullable=False)  # retain | summarize
    topic: Mapped[str] = mapped_column(String(64), nullable=False, default="general")
    source_message_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    supersedes_item_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class MemoryDecision(Base):
    __tablename__ = "memory_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("conversation_sessions.id", ondelete="SET NULL"), nullable=True)
    candidate_text: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)  # retain | summarize | discard
    category: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    topic: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    source_message_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    user_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

