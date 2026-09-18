import enum
from datetime import date, datetime
from app.core.clock import utcnow_naive

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class WorkOrderStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


# Status que já baixaram estoque / dispararam comprovante — fechar de novo
# não deve repetir nem a baixa nem a notificação (ver work_order_routes.py).
CLOSED_STATUSES = {WorkOrderStatus.DONE, WorkOrderStatus.CANCELLED}


class WorkOrderItemKind(str, enum.Enum):
    PART = "PART"
    SERVICE = "SERVICE"


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)
    appointment_id: Mapped[int | None] = mapped_column(
        ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True
    )
    mechanic_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    status: Mapped[WorkOrderStatus] = mapped_column(
        Enum(WorkOrderStatus, native_enum=False, length=20), default=WorkOrderStatus.OPEN
    )
    description: Mapped[str] = mapped_column(String(1000), default="")
    diagnosis: Mapped[str] = mapped_column(String(2000), default="")
    labor_value: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    discount_value: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    # Data da próxima revisão recomendada, usada tanto no comprovante quanto
    # no alerta automático de "revisão prestes a vencer" (ver
    # app/services/notifications.py -> check_upcoming_revisions).
    next_revision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    revision_reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    items: Mapped[list["WorkOrderItem"]] = relationship(back_populates="work_order", cascade="all, delete-orphan")
    checklist_items: Mapped[list["WorkOrderChecklistItem"]] = relationship(
        back_populates="work_order", cascade="all, delete-orphan", order_by="WorkOrderChecklistItem.id"
    )


class WorkOrderItem(Base):
    __tablename__ = "work_order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    work_order_id: Mapped[int] = mapped_column(ForeignKey("work_orders.id", ondelete="CASCADE"), index=True)
    stock_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("stock_items.id", ondelete="SET NULL"), nullable=True
    )

    kind: Mapped[WorkOrderItemKind] = mapped_column(Enum(WorkOrderItemKind, native_enum=False, length=10))
    description: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    work_order: Mapped["WorkOrder"] = relationship(back_populates="items")


class ChecklistItemStatus(str, enum.Enum):
    NOT_CHECKED = "NOT_CHECKED"
    OK = "OK"
    ATTENTION = "ATTENTION"


class WorkOrderChecklistItem(Base):
    """Item de checklist de inspeção veicular dentro de uma OS (ex.: freios,
    pneus, óleo, fluidos). Fica separado de WorkOrderItem porque não tem
    preço/quantidade — é só um veredito (OK/ATENÇÃO/não verificado) mais uma
    observação livre, para o cliente conferir o que foi inspecionado."""

    __tablename__ = "work_order_checklist_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    work_order_id: Mapped[int] = mapped_column(ForeignKey("work_orders.id", ondelete="CASCADE"), index=True)

    description: Mapped[str] = mapped_column(String(255))
    status: Mapped[ChecklistItemStatus] = mapped_column(
        Enum(ChecklistItemStatus, native_enum=False, length=15), default=ChecklistItemStatus.NOT_CHECKED
    )
    notes: Mapped[str] = mapped_column(String(500), default="")
    checked_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)

    work_order: Mapped["WorkOrder"] = relationship(back_populates="checklist_items")
