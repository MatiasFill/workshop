from datetime import datetime

from pydantic import BaseModel


class RetentionCandidate(BaseModel):
    id: int
    name: str
    last_activity_at: datetime | None
    created_at: datetime


class PurgeNotificationsResult(BaseModel):
    deleted_count: int


class AnonymizeInactiveResult(BaseModel):
    anonymized_count: int
    customer_ids: list[int]
