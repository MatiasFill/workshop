from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from app.models.finance import CashMovementType, CashSessionStatus


class CashSessionOpenRequest(BaseModel):
    opening_amount: float = Field(default=0, ge=0)
    notes: str = Field(default="", max_length=500)


class CashSessionCloseRequest(BaseModel):
    closing_amount_counted: float = Field(ge=0)
    notes: str = Field(default="", max_length=500)


class CashMovementCreate(BaseModel):
    """Movimento manual (reforço ou sangria). Recebimentos/pagamentos de
    contas passam por POST /finance/entries/{id}/pay, não por aqui."""

    type: CashMovementType
    amount: float = Field(gt=0)
    description: str = Field(default="", max_length=255)


class CashMovementResponse(BaseModel):
    id: int
    type: CashMovementType
    amount: float
    description: str
    finance_entry_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CashSessionResponse(BaseModel):
    id: int
    status: CashSessionStatus
    opening_amount: float
    opened_at: datetime
    closing_amount_expected: float | None
    closing_amount_counted: float | None
    cash_difference: float | None  # counted - expected; positivo = sobra, negativo = quebra de caixa
    closed_at: datetime | None
    notes: str
    current_balance: float  # opening_amount + movimentos até agora (só relevante enquanto OPEN)

    model_config = ConfigDict(from_attributes=True)
