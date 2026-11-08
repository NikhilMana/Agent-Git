from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class RepositoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = None
    default_branch: Optional[str] = "main"


class RepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    default_branch: str
    created_at: datetime
