from datetime import datetime

from pydantic import BaseModel

from app.models.notification_queue import NotificationRequestStatus


class NotificationQueueEntryResponse(BaseModel):
    id: int
    idempotency_key: str
    channel: str
    type: str
    status: NotificationRequestStatus
    customer_id: int | None
    work_order_id: int | None
    attempts: int
    max_attempts: int
    next_attempt_at: datetime
    last_error: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProcessQueueResult(BaseModel):
    sent: int
    failed_retry: int
    given_up: int
