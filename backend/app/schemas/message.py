from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.common import RoleEnum


class MessageCreate(BaseModel):
    role: RoleEnum
    content: str = Field(..., min_length=1)
    metadata_json: Optional[Dict[str, Any]] = None


class MessageBatchCreate(BaseModel):
    messages: List[MessageCreate] = Field(..., min_length=1)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None


class MessageBatchResponse(BaseModel):
    session_id: str
    messages: List[MessageResponse]
