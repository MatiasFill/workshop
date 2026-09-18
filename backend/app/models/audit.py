from datetime import datetime
from app.core.clock import utcnow_naive

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AuditLog(Base):
    """Trilha de auditoria de ações sensíveis: login/logout, dinheiro
    mudando de mão (pagamento/recebimento, abertura/fechamento de caixa),
    e transições de estado que baixam ou repõem estoque (fechar OS, receber
    pedido de compra). Existe tanto para investigar incidentes operacionais
    quanto para o registro de operações de tratamento de dados que a LGPD
    recomenda (art. 37).

    Só é criada (INSERT) pelo serviço em app/services/audit.py — a
    aplicação nunca edita nem apaga uma linha existente."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    action: Mapped[str] = mapped_column(String(100))  # ex.: "work_order.close", "auth.login"
    entity_type: Mapped[str] = mapped_column(String(50), default="")  # ex.: "work_order", "finance_entry"
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[str] = mapped_column(String(1000), default="")
    ip_address: Mapped[str] = mapped_column(String(45), default="")  # cabe IPv6

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)
