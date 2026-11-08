from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.message import MessageResponse


class SessionCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: Optional[str] = None
    created_at: datetime


class SessionDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: Optional[str] = None
    created_at: datetime
    messages: List[MessageResponse] = []
