from enum import Enum
from pydantic import BaseModel


class RoleEnum(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class RetentionAction(str, Enum):
    RETAIN = "retain"
    SUMMARIZE = "summarize"
    DISCARD = "discard"


class MemoryCategory(str, Enum):
    FACT = "fact"
    PREFERENCE = "preference"
    DECISION = "decision"
    CONSTRAINT = "constraint"
    TASK = "task"
    SUMMARY = "summary"
    OTHER = "other"


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail

