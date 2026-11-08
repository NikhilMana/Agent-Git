from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    actor: str
    entity_id: Optional[str] = None
    payload_json: Dict[str, Any]
    created_at: datetime
