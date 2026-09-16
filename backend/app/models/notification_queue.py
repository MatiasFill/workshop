import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.notification import NotificationChannel, NotificationType


class NotificationRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    SKIPPED = "SKIPPED"  # sem SMTP/WhatsApp configurado, ou cliente sem contato — não adianta retentar
    FAILED = "FAILED"  # falhou, ainda dentro do limite de tentativas — será retentado
    GIVEN_UP = "GIVEN_UP"  # esgotou as tentativas


class NotificationRequest(Base):
    """Fila de reenvio com retry/backoff e idempotência (FASE 11).

    Só entra aqui uma notificação que **falhou** no envio imediato (ver
    app/services/notifications.py) — o caminho feliz continua síncrono,
    como nas FASES 4/5. `idempotency_key` garante que a mesma notificação
    lógica (ex.: "comprovante da OS #42 por e-mail") nunca seja enfileirada
    duas vezes, mesmo que a rota que a disparou seja chamada de novo antes
    do reprocessamento.

    Diferente de `NotificationLog` (FASE 4/5, histórico de cada tentativa),
    esta tabela é o estado atual do reenvio — uma linha por notificação
    lógica pendente, não uma por tentativa."""

    __tablename__ = "notification_requests"
    __table_args__ = (
        UniqueConstraint("company_id", "idempotency_key", name="uq_notification_requests_company_idem_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(200))

    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel, native_enum=False, length=20))
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType, native_enum=False, length=30))
    status: Mapped[NotificationRequestStatus] = mapped_column(
        Enum(NotificationRequestStatus, native_enum=False, length=10), default=NotificationRequestStatus.PENDING
    )

    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    work_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("work_orders.id", ondelete="SET NULL"), nullable=True
    )

    subject: Mapped[str] = mapped_column(String(255), default="")
    message: Mapped[str] = mapped_column(String(2000), default="")

    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_error: Mapped[str] = mapped_column(String(500), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
