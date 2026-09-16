from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_db, require_permission
from app.core.sessions import SessionData
from app.models.appointment import Appointment, AppointmentStatus, BLOCKING_STATUSES
from app.models.customer import Customer, Vehicle
from app.schemas.appointment import AppointmentCreate, AppointmentResponse, AppointmentUpdate

appointment_router = APIRouter()

# Mesmo princípio das outras rotas da FASE 2: company_id vem sempre da sessão
# autenticada (user.company_id), nunca do corpo da requisição.


def _to_response(db: Session, appt: Appointment) -> AppointmentResponse:
    customer = db.query(Customer).filter(Customer.id == appt.customer_id).first()
    vehicle = (
        db.query(Vehicle).filter(Vehicle.id == appt.vehicle_id).first()
        if appt.vehicle_id
        else None
    )
    return AppointmentResponse(
        id=appt.id,
        company_id=appt.company_id,
        branch_id=appt.branch_id,
        customer_id=appt.customer_id,
        vehicle_id=appt.vehicle_id,
        mechanic_id=appt.mechanic_id,
        scheduled_at=appt.scheduled_at,
        duration_minutes=appt.duration_minutes,
        status=appt.status,
        service_type=appt.service_type,
        notes=appt.notes,
        created_at=appt.created_at,
        customer_name=customer.name if customer else "",
        vehicle_plate=vehicle.plate if vehicle else "",
    )


def _get_appointment_or_404(db: Session, company_id: int, appointment_id: int) -> Appointment:
    appt = (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id, Appointment.company_id == company_id)
        .first()
    )
    if not appt:
        raise HTTPException(404, "Agendamento não encontrado.")
    return appt


def _assert_customer_and_vehicle_belong_to_company(
    db: Session, company_id: int, customer_id: int, vehicle_id: int | None
) -> None:
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.company_id == company_id)
        .first()
    )
    if not customer:
        raise HTTPException(404, "Cliente não encontrado.")

    if vehicle_id is not None:
        vehicle = (
            db.query(Vehicle)
            .filter(Vehicle.id == vehicle_id, Vehicle.company_id == company_id)
            .first()
        )
        if not vehicle:
            raise HTTPException(404, "Veículo não encontrado.")
        if vehicle.customer_id != customer_id:
            raise HTTPException(422, "Este veículo não pertence ao cliente informado.")


def _assert_no_conflict(
    db: Session,
    company_id: int,
    mechanic_id: int | None,
    scheduled_at: datetime,
    duration_minutes: int,
    exclude_id: int | None = None,
) -> None:
    """Um mesmo mecânico não pode ter dois agendamentos com horários que se
    sobrepõem. Sem mecânico atribuído, não há como checar conflito (a agenda
    "geral" da oficina, por unidade, fica para uma fase futura de capacidade
    por baia/box), então a checagem é só feita quando `mechanic_id` existe."""
    if mechanic_id is None:
        return

    new_start = scheduled_at
    new_end = scheduled_at + timedelta(minutes=duration_minutes)

    query = db.query(Appointment).filter(
        Appointment.company_id == company_id,
        Appointment.mechanic_id == mechanic_id,
        Appointment.status.in_(BLOCKING_STATUSES),
    )
    if exclude_id is not None:
        query = query.filter(Appointment.id != exclude_id)

    for other in query.all():
        other_start = other.scheduled_at
        other_end = other.scheduled_at + timedelta(minutes=other.duration_minutes)
        if new_start < other_end and other_start < new_end:
            raise HTTPException(
                409,
                f"Conflito de horário: o mecânico já tem o agendamento #{other.id} "
                f"das {other_start.strftime('%d/%m %H:%M')} às {other_end.strftime('%H:%M')}.",
            )


@appointment_router.get("/appointments", response_model=list[AppointmentResponse])
def list_appointments(
    user: SessionData = Depends(require_permission("appointments.read")),
    db: Session = Depends(get_tenant_db),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    mechanic_id: int | None = Query(default=None),
    customer_id: int | None = Query(default=None),
    status: AppointmentStatus | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(Appointment).filter(Appointment.company_id == user.company_id)
    if date_from is not None:
        query = query.filter(Appointment.scheduled_at >= date_from)
    if date_to is not None:
        query = query.filter(Appointment.scheduled_at <= date_to)
    if mechanic_id is not None:
        query = query.filter(Appointment.mechanic_id == mechanic_id)
    if customer_id is not None:
        query = query.filter(Appointment.customer_id == customer_id)
    if status is not None:
        query = query.filter(Appointment.status == status)

    rows = query.order_by(Appointment.scheduled_at.asc()).offset(offset).limit(limit).all()
    return [_to_response(db, appt) for appt in rows]


@appointment_router.post("/appointments", response_model=AppointmentResponse, status_code=201)
def create_appointment(
    payload: AppointmentCreate,
    user: SessionData = Depends(require_permission("appointments.create")),
    db: Session = Depends(get_tenant_db),
):
    _assert_customer_and_vehicle_belong_to_company(db, user.company_id, payload.customer_id, payload.vehicle_id)
    _assert_no_conflict(db, user.company_id, payload.mechanic_id, payload.scheduled_at, payload.duration_minutes)

    appt = Appointment(
        company_id=user.company_id,
        branch_id=payload.branch_id,
        customer_id=payload.customer_id,
        vehicle_id=payload.vehicle_id,
        mechanic_id=payload.mechanic_id,
        scheduled_at=payload.scheduled_at,
        duration_minutes=payload.duration_minutes,
        service_type=payload.service_type.strip(),
        notes=payload.notes.strip(),
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return _to_response(db, appt)


@appointment_router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    user: SessionData = Depends(require_permission("appointments.read")),
    db: Session = Depends(get_tenant_db),
):
    appt = _get_appointment_or_404(db, user.company_id, appointment_id)
    return _to_response(db, appt)


@appointment_router.patch("/appointments/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    payload: AppointmentUpdate,
    user: SessionData = Depends(require_permission("appointments.update")),
    db: Session = Depends(get_tenant_db),
):
    appt = _get_appointment_or_404(db, user.company_id, appointment_id)
    data = payload.model_dump(exclude_unset=True)

    if "vehicle_id" in data and data["vehicle_id"] is not None:
        _assert_customer_and_vehicle_belong_to_company(db, user.company_id, appt.customer_id, data["vehicle_id"])

    # Só reavalia conflito se horário, duração ou mecânico mudarem — evita
    # falso-positivo comparando o próprio agendamento contra si mesmo (por
    # isso exclude_id) e evita trabalho à toa quando nada relevante mudou.
    if {"scheduled_at", "duration_minutes", "mechanic_id"} & data.keys():
        new_scheduled_at = data.get("scheduled_at", appt.scheduled_at)
        new_duration = data.get("duration_minutes", appt.duration_minutes)
        new_mechanic_id = data.get("mechanic_id", appt.mechanic_id)
        _assert_no_conflict(
            db, user.company_id, new_mechanic_id, new_scheduled_at, new_duration, exclude_id=appt.id
        )

    for field in ("service_type", "notes"):
        if field in data and isinstance(data[field], str):
            data[field] = data[field].strip()

    for key, value in data.items():
        setattr(appt, key, value)

    db.commit()
    db.refresh(appt)
    return _to_response(db, appt)


@appointment_router.post("/appointments/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: int,
    user: SessionData = Depends(require_permission("appointments.cancel")),
    db: Session = Depends(get_tenant_db),
):
    appt = _get_appointment_or_404(db, user.company_id, appointment_id)
    appt.status = AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(appt)
    return _to_response(db, appt)
