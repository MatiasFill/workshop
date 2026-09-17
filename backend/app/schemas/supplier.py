from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.validators import validate_document, validate_email, validate_phone


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    document: str = Field(default="", max_length=20)
    phone: str = Field(default="", max_length=30)
    email: str = Field(default="", max_length=255)
    notes: str = Field(default="", max_length=1000)

    _document = field_validator("document")(validate_document)
    _phone = field_validator("phone")(validate_phone)
    _email = field_validator("email")(validate_email)


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    document: str | None = Field(default=None, max_length=20)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None

    @field_validator("document")
    @classmethod
    def normalize_document(cls, value: str | None) -> str | None:
        return None if value is None else validate_document(value, None)

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        return None if value is None else validate_phone(value, None)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        return None if value is None else validate_email(value, None)


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
