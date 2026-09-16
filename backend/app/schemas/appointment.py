from datetime import datetime

from pydantic import BaseModel, Field

from app.models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    customer_id: int
    vehicle_id: int | None = None
    mechanic_id: int | None = None
    branch_id: int | None = None
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=15, le=480)
    service_type: str = Field(default="", max_length=255)
    notes: str = Field(default="", max_length=1000)


class AppointmentUpdate(BaseModel):
    vehicle_id: int | None = None
    mechanic_id: int | None = None
    branch_id: int | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=15, le=480)
    status: AppointmentStatus | None = None
    service_type: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=1000)


class AppointmentResponse(BaseModel):
    id: int
    company_id: int
    branch_id: int | None
    customer_id: int
    vehicle_id: int | None
    mechanic_id: int | None
    scheduled_at: datetime
    duration_minutes: int
    status: AppointmentStatus
    service_type: str
    notes: str
    created_at: datetime

    # Enriquecimento de leitura, para a agenda não precisar de N chamadas
    # extras só para mostrar nome do cliente/veículo na tela. Sempre montado
    # explicitamente pelas rotas (ver app/api/appointment_routes.py) — não
    # depende de atributos "mágicos" no objeto ORM.
    customer_name: str = ""
    vehicle_plate: str = ""

    class Config:
        from_attributes = True
