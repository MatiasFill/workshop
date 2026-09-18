from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    detail: str
    ip_address: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
