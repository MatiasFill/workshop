from pydantic import BaseModel, Field

# Nota: usamos "str" em vez de "EmailStr" de propósito, para não adicionar a
# dependência "email-validator" ao projeto só por causa deste campo. A
# validação de formato de e-mail de verdade acontece no cadastro do usuário
# (fora do escopo da FASE 1); aqui só validamos presença e tamanho.


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=255)


class MeResponse(BaseModel):
    user_id: int
    company_id: int
    branch_id: int | None
    name: str
    email: str
    permissions: list[str]
