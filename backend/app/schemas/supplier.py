from datetime import datetime

from pydantic import BaseModel, Field


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    document: str = Field(default="", max_length=20)
    phone: str = Field(default="", max_length=30)
    email: str = Field(default="", max_length=255)
    notes: str = Field(default="", max_length=1000)


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    document: str | None = Field(default=None, max_length=20)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None


class SupplierResponse(BaseModel):
    id: int
    name: str
    document: str
    phone: str
    email: str
    notes: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
