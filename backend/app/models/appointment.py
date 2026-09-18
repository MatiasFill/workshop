import enum
from datetime import datetime
from app.core.clock import utcnow_naive

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


# Status que "ocupam" a agenda do mecânico para fins de detecção de conflito.
# CANCELLED e NO_SHOW liberam o horário de propósito — um agendamento
# cancelado não deveria travar um novo agendamento no mesmo horário.
BLOCKING_STATUSES = {
    AppointmentStatus.SCHEDULED,
    AppointmentStatus.CONFIRMED,
    AppointmentStatus.IN_PROGRESS,
}


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)
    mechanic_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    scheduled_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)

    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, native_enum=False, length=20), default=AppointmentStatus.SCHEDULED
    )
    service_type: Mapped[str] = mapped_column(String(255), default="")
    notes: Mapped[str] = mapped_column(String(1000), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)

    customer: Mapped["Customer"] = relationship()  # noqa: F821 — import cíclico evitado via string
    vehicle: Mapped["Vehicle | None"] = relationship()  # noqa: F821
