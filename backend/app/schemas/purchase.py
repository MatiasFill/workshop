from datetime import date, datetime

from pydantic import BaseModel, Field, ConfigDict

from app.models.purchase import PurchaseOrderStatus


class PurchaseOrderItemCreate(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    stock_item_id: int | None = None
    quantity: int = Field(default=1, ge=1)
    unit_cost: float = Field(default=0, ge=0)


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    notes: str = Field(default="", max_length=1000)
    payment_due_date: date | None = None
    items: list[PurchaseOrderItemCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)
    payment_due_date: date | None = None


class PurchaseOrderItemResponse(BaseModel):
    id: int
    description: str
    stock_item_id: int | None
    quantity: int
    unit_cost: float
    total_cost: float

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderResponse(BaseModel):
    id: int
    supplier_id: int
    supplier_name: str = ""
    status: PurchaseOrderStatus
    notes: str
    payment_due_date: date | None
    total_value: float
    created_at: datetime
    ordered_at: datetime | None
    received_at: datetime | None
    items: list[PurchaseOrderItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
