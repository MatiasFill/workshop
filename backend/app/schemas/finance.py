from datetime import date, datetime

from pydantic import BaseModel, Field, ConfigDict

from app.models.finance import FinanceEntryStatus, FinanceEntryType


class FinanceEntryCreate(BaseModel):
    type: FinanceEntryType
    category: str = Field(default="", max_length=100)
    description: str = Field(default="", max_length=500)
    amount: float = Field(gt=0)
    due_date: date
    customer_id: int | None = None


class FinanceEntryUpdate(BaseModel):
    category: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    amount: float | None = Field(default=None, gt=0)
    due_date: date | None = None


class FinanceEntryPayRequest(BaseModel):
    """Registra o pagamento/recebimento. `amount` é opcional — se omitido,
    quita o valor total (`FinanceEntry.amount`); um valor menor deixa a
    conta com o saldo restante ainda em aberto (pagamento parcial)."""

    amount: float | None = Field(default=None, gt=0)
    register_cash_movement: bool = Field(
        default=True, description="Se true e houver caixa aberto, lança um CashMovement correspondente."
    )


class FinanceEntryResponse(BaseModel):
    id: int
    type: FinanceEntryType
    status: FinanceEntryStatus
    category: str
    description: str
    amount: float
    due_date: date
    paid_amount: float
    remaining_amount: float
    paid_at: datetime | None
    customer_id: int | None
    customer_name: str = ""
    work_order_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
