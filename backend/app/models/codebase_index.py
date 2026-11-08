import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, utc_now


class RepositoryIndexMeta(Base):
    __tablename__ = "repository_index_meta"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), unique=True, nullable=False)
    canonical_root: Mapped[str] = mapped_column(String(512), nullable=False)
    last_indexed_commit: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    index_version: Mapped[str] = mapped_column(String(32), default="2.0.0", nullable=False)

    files: Mapped[List["CodebaseFileRecord"]] = relationship(
        "CodebaseFileRecord",
        back_populates="index_meta",
        cascade="all, delete-orphan"
    )


class CodebaseFileRecord(Base):
    __tablename__ = "codebase_file_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    index_meta_id: Mapped[str] = mapped_column(String(36), ForeignKey("repository_index_meta.id", ondelete="CASCADE"), nullable=False)
    relative_path: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    last_indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    indexed_commit: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    index_meta: Mapped["RepositoryIndexMeta"] = relationship("RepositoryIndexMeta", back_populates="files")
    symbols: Mapped[List["CodebaseSymbolRecord"]] = relationship(
        "CodebaseSymbolRecord",
        back_populates="file_record",
        cascade="all, delete-orphan"
    )


class CodebaseSymbolRecord(Base):
    __tablename__ = "codebase_symbol_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_record_id: Mapped[str] = mapped_column(String(36), ForeignKey("codebase_file_records.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)  # class | function | method | interface | constant
    line_start: Mapped[int] = mapped_column(Integer, nullable=False)
    line_end: Mapped[int] = mapped_column(Integer, nullable=False)
    signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    docstring: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    file_record: Mapped["CodebaseFileRecord"] = relationship("CodebaseFileRecord", back_populates="symbols")


class CodebaseDependencyRecord(Base):
    __tablename__ = "codebase_dependency_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    source_path: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    target_path: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    relation: Mapped[str] = mapped_column(String(64), nullable=False)  # imports | calls | extends | references
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

