import enum
from datetime import datetime
from app.core.clock import utcnow_naive

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class NotificationChannel(str, enum.Enum):
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"


class NotificationType(str, enum.Enum):
    WORK_ORDER_RECEIPT = "WORK_ORDER_RECEIPT"
    REVISION_REMINDER = "REVISION_REMINDER"


class NotificationStatus(str, enum.Enum):
    SENT = "SENT"
    SKIPPED = "SKIPPED"  # sem SMTP/WhatsApp configurado, ou cliente sem contato cadastrado
    FAILED = "FAILED"


class NotificationLog(Base):
    """Registro de toda tentativa de notificação (comprovante de OS, alerta de
    revisão), enviada ou não — para auditoria e para a tela de Relatórios."""

    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    work_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("work_orders.id", ondelete="SET NULL"), nullable=True
    )

    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel, native_enum=False, length=20))
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType, native_enum=False, length=30))
    status: Mapped[NotificationStatus] = mapped_column(Enum(NotificationStatus, native_enum=False, length=10))
    detail: Mapped[str] = mapped_column(String(500), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)
