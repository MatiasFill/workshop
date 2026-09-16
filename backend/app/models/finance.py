import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class FinanceEntryType(str, enum.Enum):
    PAYABLE = "PAYABLE"  # conta a pagar (fornecedor, despesa)
    RECEIVABLE = "RECEIVABLE"  # conta a receber (cliente, OS)


class FinanceEntryStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    OVERDUE = "OVERDUE"  # calculado na leitura (due_date < hoje e ainda PENDING), não armazenado à parte
    CANCELLED = "CANCELLED"


class CashSessionStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class CashMovementType(str, enum.Enum):
    IN = "IN"  # recebimento, reforço de caixa
    OUT = "OUT"  # pagamento, sangria


class FinanceEntry(Base):
    """Conta a pagar ou a receber. Uma OS concluída (ver
    app/api/work_order_routes.py) cria automaticamente uma RECEIVABLE
    pendente aqui — o pagamento em si é registrado à parte via
    POST /finance/entries/{id}/pay (que também lança um CashMovement se
    houver caixa aberto)."""

    __tablename__ = "finance_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)

    type: Mapped[FinanceEntryType] = mapped_column(Enum(FinanceEntryType, native_enum=False, length=20))
    status: Mapped[FinanceEntryStatus] = mapped_column(
        Enum(FinanceEntryStatus, native_enum=False, length=20), default=FinanceEntryStatus.PENDING
    )

    category: Mapped[str] = mapped_column(String(100), default="")
    description: Mapped[str] = mapped_column(String(500), default="")
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    due_date: Mapped[date] = mapped_column(Date)

    paid_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    work_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("work_orders.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CashSession(Base):
    """Sessão de caixa (abertura/fechamento diário). Só pode haver uma
    sessão OPEN por empresa+filial por vez — checado na rota, não no banco,
    para manter a migration simples neste scaffold."""

    __tablename__ = "cash_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)

    status: Mapped[CashSessionStatus] = mapped_column(
        Enum(CashSessionStatus, native_enum=False, length=10), default=CashSessionStatus.OPEN
    )
    opening_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    opened_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Preenchidos só no fechamento. `closing_amount_counted` é o que a pessoa
    # contou fisicamente na gaveta; `closing_amount_expected` é
    # opening_amount + soma dos CashMovement — a diferença entre os dois é a
    # "quebra de caixa" (para mais ou para menos).
    closing_amount_expected: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    closing_amount_counted: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    notes: Mapped[str] = mapped_column(String(500), default="")

    movements: Mapped[list["CashMovement"]] = relationship(back_populates="cash_session", cascade="all, delete-orphan")


class CashMovement(Base):
    """Toda entrada/saída física do caixa: recebimento de uma conta a
    receber, pagamento de uma conta a pagar, reforço ou sangria manual."""

    __tablename__ = "cash_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    cash_session_id: Mapped[int] = mapped_column(ForeignKey("cash_sessions.id", ondelete="CASCADE"), index=True)
    finance_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("finance_entries.id", ondelete="SET NULL"), nullable=True
    )

    type: Mapped[CashMovementType] = mapped_column(Enum(CashMovementType, native_enum=False, length=10))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))  # sempre positivo; `type` indica a direção
    description: Mapped[str] = mapped_column(String(255), default="")

    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cash_session: Mapped["CashSession"] = relationship(back_populates="movements")
