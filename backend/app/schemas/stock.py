from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.stock import StockMovementType


class StockItemCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    unit: str = Field(default="un", max_length=20)
    quantity: int = Field(default=0, ge=0)
    min_quantity: int = Field(default=0, ge=0)
    cost_price: float = Field(default=0, ge=0)
    sale_price: float = Field(default=0, ge=0)
    notes: str = Field(default="", max_length=1000)

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, v: str) -> str:
        return v.strip().upper()


class StockItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    unit: str | None = Field(default=None, max_length=20)
    min_quantity: int | None = Field(default=None, ge=0)
    cost_price: float | None = Field(default=None, ge=0)
    sale_price: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None


class StockAdjustRequest(BaseModel):
    """Ajuste manual de quantidade (entrada, saída ou correção de contagem).
    Baixas automáticas por fechamento de OS não passam por aqui — ver
    app/api/work_order_routes.py."""

    type: StockMovementType
    quantity: int = Field(gt=0)
    reason: str = Field(default="", max_length=255)


class StockItemResponse(BaseModel):
    id: int
    sku: str
    name: str
    unit: str
    quantity: int
    min_quantity: int
    cost_price: float
    sale_price: float
    notes: str
    is_active: bool
    is_low_stock: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StockMovementResponse(BaseModel):
    id: int
    stock_item_id: int
    work_order_id: int | None
    type: StockMovementType
    quantity: int
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True
