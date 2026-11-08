from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.memory import MemoryItemCreate


class SnapshotItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    memory_item_id: str
    logical_key: Optional[str] = None
    content_at_commit: str
    category_at_commit: str
    topic_at_commit: str
    source_message_ids: List[str]
    retention_action_at_commit: str
    confidence_at_commit: Optional[float] = None
    rationale_at_commit: Optional[str] = None


class CommitCreate(BaseModel):
    branch: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    items: List[MemoryItemCreate] = Field(..., min_length=1)
    author: Optional[str] = "user"


class CommitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    repository_id: str
    branch_id: str
    parent_commit_ids: List[str]
    message: str
    snapshot_hash: str
    created_at: datetime
    author: str
    items: Optional[List[SnapshotItemResponse]] = None


class CommitDiffResponse(BaseModel):
    base_commit_id: str
    target_commit_id: str
    added_items: List[SnapshotItemResponse]
    removed_items: List[SnapshotItemResponse]
    modified_items: List[Dict[str, Any]]
