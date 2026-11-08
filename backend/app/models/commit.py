import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, utc_now


class Commit(Base):
    __tablename__ = "commits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    parent_commit_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    author: Mapped[str] = mapped_column(String(64), default="user", nullable=False)

    repository: Mapped["Repository"] = relationship("Repository", back_populates="commits")
    branch: Mapped["Branch"] = relationship("Branch")
    snapshot_items: Mapped[List["SnapshotItem"]] = relationship(
        "SnapshotItem",
        back_populates="commit",
        cascade="all, delete-orphan",
        order_by="SnapshotItem.memory_item_id"
    )

