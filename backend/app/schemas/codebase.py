from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CodebaseFileSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    relative_path: str
    language: str
    size_bytes: int
    content_hash: str
    is_stale: bool = False
    summary: Optional[str] = None


class CodebaseSymbolSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    kind: str
    file: str
    line_start: int
    line_end: int
    signature: Optional[str] = None
    docstring: Optional[str] = None


class CodebaseDependencySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_path: str
    target_path: str
    relation: str
    confidence: float = 1.0


class CodebaseIndexStatus(BaseModel):
    repository_id: str
    canonical_root: str
    total_files: int
    total_symbols: int
    total_dependencies: int
    last_indexed_at: Optional[datetime] = None
    last_indexed_commit: Optional[str] = None
    index_version: str = "2.0.0"


class IndexRefreshReport(BaseModel):
    repository_id: str
    indexed_count: int
    skipped_count: int
    deleted_count: int
    stale_count: int
    duration_ms: float

