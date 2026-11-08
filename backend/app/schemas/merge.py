from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.common import ErrorDetail


class MergeRequest(BaseModel):
    source_branch: str = Field(..., min_length=1)
    target_branch: str = Field(..., min_length=1)
    selected_memory_item_ids: List[str] = Field(..., min_length=1)
    message: Optional[str] = None


class MergeConflictDetail(BaseModel):
    logical_key: str
    source_item: Dict[str, Any]
    target_item: Dict[str, Any]
    conflict_reason: str


class MergeConflictResponse(BaseModel):
    error: ErrorDetail
    conflicts: List[MergeConflictDetail]
