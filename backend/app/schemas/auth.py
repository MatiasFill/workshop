from pydantic import BaseModel, Field, field_validator

from app.core.validators import validate_email


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_login_email(cls, value: str) -> str:
        return validate_email(value, None)


class MeResponse(BaseModel):
    user_id: int
    company_id: int
    branch_id: int | None
    name: str
    email: str
    permissions: list[str]
