from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.commit import CommitResponse


class BranchCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    from_commit_id: Optional[str] = None


class BranchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    repository_id: str
    name: str
    head_commit_id: Optional[str] = None
    created_from_commit_id: Optional[str] = None
    created_at: datetime


class BranchHistoryResponse(BaseModel):
    branch: str
    commits: List[CommitResponse]


class RestoreRequest(BaseModel):
    commit_id: str
    message: Optional[str] = "Restore historical snapshot"
