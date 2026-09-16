from datetime import date, datetime

from pydantic import BaseModel


class CustomerExportVehicle(BaseModel):
    id: int
    plate: str
    brand: str
    model: str
    year: int | None
    color: str


class CustomerExportAppointment(BaseModel):
    id: int
    scheduled_at: datetime
    status: str
    service_type: str


class CustomerExportWorkOrderItem(BaseModel):
    description: str
    quantity: int
    unit_price: float


class CustomerExportWorkOrder(BaseModel):
    id: int
    status: str
    total_value: float
    created_at: datetime
    closed_at: datetime | None
    items: list[CustomerExportWorkOrderItem]


class CustomerExportFinanceEntry(BaseModel):
    id: int
    type: str
    status: str
    amount: float
    due_date: date
    paid_amount: float


class CustomerExportNotification(BaseModel):
    channel: str
    type: str
    status: str
    created_at: datetime


class CustomerExportInfo(BaseModel):
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


class CustomerDataExport(BaseModel):
    customer: CustomerExportInfo
    vehicles: list[CustomerExportVehicle]
    appointments: list[CustomerExportAppointment]
    work_orders: list[CustomerExportWorkOrder]
    finance_entries: list[CustomerExportFinanceEntry]
    notifications: list[CustomerExportNotification]
    exported_at: datetime


class AnonymizeResult(BaseModel):
    id: int
    is_anonymized: bool
    anonymized_at: datetime | None
