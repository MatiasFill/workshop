from datetime import date, datetime

from pydantic import BaseModel, Field, ConfigDict

from app.models.work_order import ChecklistItemStatus, WorkOrderItemKind, WorkOrderStatus


class WorkOrderItemCreate(BaseModel):
    kind: WorkOrderItemKind
    description: str = Field(min_length=1, max_length=255)
    stock_item_id: int | None = None
    quantity: int = Field(default=1, ge=1)
    unit_price: float = Field(default=0, ge=0)


class WorkOrderCreate(BaseModel):
    customer_id: int
    vehicle_id: int | None = None
    appointment_id: int | None = None
    mechanic_id: int | None = None
    description: str = Field(default="", max_length=1000)
    diagnosis: str = Field(default="", max_length=2000)
    labor_value: float = Field(default=0, ge=0)
    discount_value: float = Field(default=0, ge=0)
    next_revision_date: date | None = None
    items: list[WorkOrderItemCreate] = Field(default_factory=list)


class WorkOrderUpdate(BaseModel):
    mechanic_id: int | None = None
    status: WorkOrderStatus | None = None
    description: str | None = Field(default=None, max_length=1000)
    diagnosis: str | None = Field(default=None, max_length=2000)
    labor_value: float | None = Field(default=None, ge=0)
    discount_value: float | None = Field(default=None, ge=0)
    next_revision_date: date | None = None


class WorkOrderItemAdd(WorkOrderItemCreate):
    pass


class WorkOrderItemResponse(BaseModel):
    id: int
    kind: WorkOrderItemKind
    description: str
    stock_item_id: int | None
    quantity: int
    unit_price: float
    total_price: float

    model_config = ConfigDict(from_attributes=True)


class ChecklistItemCreate(BaseModel):
    description: str = Field(min_length=1, max_length=255)


class ChecklistItemUpdate(BaseModel):
    status: ChecklistItemStatus | None = None
    notes: str | None = Field(default=None, max_length=500)


class ChecklistItemResponse(BaseModel):
    id: int
    description: str
    status: ChecklistItemStatus
    notes: str
    checked_by_user_id: int | None
    checked_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class WorkOrderResponse(BaseModel):
    id: int
    company_id: int
    branch_id: int | None
    customer_id: int
    vehicle_id: int | None
    appointment_id: int | None
    mechanic_id: int | None
    status: WorkOrderStatus
    description: str
    diagnosis: str
    labor_value: float
    discount_value: float
    total_value: float
    next_revision_date: date | None
    created_at: datetime
    closed_at: datetime | None

    # Enriquecimento de leitura, mesmo padrão de AppointmentResponse — sempre
    # montado explicitamente pelas rotas, nunca via atributo mágico no ORM.
    customer_name: str = ""
    vehicle_plate: str = ""
    items: list[WorkOrderItemResponse] = Field(default_factory=list)
    checklist_items: list[ChecklistItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
