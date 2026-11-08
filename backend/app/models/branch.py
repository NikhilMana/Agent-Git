import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, utc_now


class Branch(Base):
    __tablename__ = "branches"
    __table_args__ = (
        UniqueConstraint("repository_id", "name", name="uq_repo_branch_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    head_commit_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_from_commit_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    repository: Mapped["Repository"] = relationship("Repository", back_populates="branches")

