import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.common import RetentionAction, MemoryCategory


class CandidatePreviewRequest(BaseModel):
    mode: Optional[str] = "deterministic"


class MemoryCandidate(BaseModel):
    candidate_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    logical_key: Optional[str] = None
    content: str
    action: RetentionAction
    category: MemoryCategory
    topic: str
    source_message_ids: List[str]
    rationale: str
    confidence: Optional[float] = 1.0


class CandidatePreviewResponse(BaseModel):
    session_id: str
    candidates: List[MemoryCandidate]


class MemoryDecisionOverrideRequest(BaseModel):
    candidate_id: Optional[str] = None
    logical_key: Optional[str] = None
    content: Optional[str] = None
    action: RetentionAction
    category: Optional[MemoryCategory] = None
    topic: Optional[str] = None
    rationale: Optional[str] = None
    source_message_ids: Optional[List[str]] = None


class MemoryItemCreate(BaseModel):
    logical_key: Optional[str] = None
    content: str
    category: MemoryCategory
    topic: str
    source_message_ids: List[str]
    rationale: str
    confidence: Optional[float] = 1.0
    retention_action: Optional[RetentionAction] = RetentionAction.RETAIN


class MemoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    repository_id: Optional[str] = None
    logical_key: Optional[str] = None
    content: str
    category: str
    retention_action: str
    topic: str
    source_message_ids: List[str]
    confidence: Optional[float] = None
    rationale: str
    created_at: datetime
    supersedes_item_id: Optional[str] = None
    is_active: bool
