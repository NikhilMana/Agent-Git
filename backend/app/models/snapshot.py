import uuid
from typing import List, Optional
from sqlalchemy import String, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class SnapshotItem(Base):
    __tablename__ = "snapshot_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    commit_id: Mapped[str] = mapped_column(String(36), ForeignKey("commits.id", ondelete="CASCADE"), nullable=False)
    memory_item_id: Mapped[str] = mapped_column(String(36), nullable=False)
    logical_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    content_at_commit: Mapped[str] = mapped_column(Text, nullable=False)
    category_at_commit: Mapped[str] = mapped_column(String(32), nullable=False)
    topic_at_commit: Mapped[str] = mapped_column(String(64), nullable=False)
    source_message_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    retention_action_at_commit: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence_at_commit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rationale_at_commit: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    commit: Mapped["Commit"] = relationship("Commit", back_populates="snapshot_items")

