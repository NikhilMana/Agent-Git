from typing import Optional, List
from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1)
    branch: Optional[str] = "main"
    top_k: Optional[int] = 5


class RetrievedMemoryItem(BaseModel):
    memory_item_id: str
    content: str
    score: float
    source_message_ids: List[str]
    topic: str
    commit_id: str
    logical_key: Optional[str] = None
    category: Optional[str] = None


class RetrievalResponse(BaseModel):
    query: str
    branch: str
    commit_id: Optional[str] = None
    results: List[RetrievedMemoryItem]
    context_text: Optional[str] = None

