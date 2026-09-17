from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.validators import (
    validate_document,
    validate_email,
    validate_phone,
    validate_plate,
)


class VehicleCreate(BaseModel):
    plate: str = Field(min_length=1, max_length=10)
    brand: str = Field(default="", max_length=100)
    model: str = Field(default="", max_length=100)
    year: int | None = Field(default=None, ge=1900, le=2100)
    color: str = Field(default="", max_length=50)
    km: int | None = Field(default=None, ge=0)
    notes: str = Field(default="", max_length=1000)

    @field_validator("plate")
    @classmethod
    def normalize_plate(cls, v: str) -> str:
        return validate_plate(v, None)


class VehicleUpdate(BaseModel):
    plate: str | None = Field(default=None, min_length=1, max_length=10)
    brand: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    year: int | None = Field(default=None, ge=1900, le=2100)
    color: str | None = Field(default=None, max_length=50)
    km: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None

    @field_validator("plate")
    @classmethod
    def normalize_plate(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_plate(v, None)


class VehicleResponse(BaseModel):
    id: int
    customer_id: int
    plate: str
    brand: str
    model: str
    year: int | None
    color: str
    km: int | None
    notes: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    document: str = Field(default="", max_length=20)
    phone: str = Field(default="", max_length=20)
    email: str = Field(default="", max_length=255)
    address: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=1000)
    vehicles: list[VehicleCreate] = Field(default_factory=list)

    @field_validator("document")
    @classmethod
    def normalize_document(cls, v: str) -> str:
        return validate_document(v, None)

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        return validate_phone(v, None)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return validate_email(v, None)


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    document: str | None = Field(default=None, max_length=20)
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None

    @field_validator("document")
    @classmethod
    def normalize_document(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_document(v, None)

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_phone(v, None)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_email(v, None)


class CustomerResponse(BaseModel):
    id: int
    name: str
    document: str
    phone: str
    email: str
    address: str
    notes: str
    is_active: bool
    is_anonymized: bool
    created_at: datetime
    vehicles: list[VehicleResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class CustomerListItem(BaseModel):
    """Versão enxuta para listagem (sem os veículos, para não pesar a página)."""

    id: int
    name: str
    document: str
    phone: str
    email: str
    is_active: bool
    is_anonymized: bool
    vehicle_count: int
    created_at: datetime

    class Config:
        from_attributes = True
