import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, utc_now


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_branch: Mapped[str] = mapped_column(String(64), default="main", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    branches: Mapped[List["Branch"]] = relationship(
        "Branch",
        back_populates="repository",
        cascade="all, delete-orphan"
    )
    commits: Mapped[List["Commit"]] = relationship(
        "Commit",
        back_populates="repository",
        cascade="all, delete-orphan"
    )

