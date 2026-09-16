from datetime import datetime

from pydantic import BaseModel

from app.models.notification import NotificationChannel, NotificationStatus, NotificationType


class NotificationLogResponse(BaseModel):
    id: int
    customer_id: int | None
    work_order_id: int | None
    channel: NotificationChannel
    type: NotificationType
    status: NotificationStatus
    detail: str
    created_at: datetime

    class Config:
        from_attributes = True


class RevisionCheckResult(BaseModel):
    reminders_sent: int
    logs: list[NotificationLogResponse]
