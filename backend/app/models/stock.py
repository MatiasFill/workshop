import enum
from datetime import datetime
from app.core.clock import utcnow_naive

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class StockMovementType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"
    ADJUSTMENT = "ADJUSTMENT"


class StockItem(Base):
    __tablename__ = "stock_items"
    __table_args__ = (
        UniqueConstraint("company_id", "sku", name="uq_stock_items_company_sku"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)

    sku: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(255))
    unit: Mapped[str] = mapped_column(String(20), default="un")  # un, l, kg, m, etc.
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    # Abaixo deste valor o item entra na lista de "estoque crítico" do dashboard.
    min_quantity: Mapped[int] = mapped_column(Integer, default=0)
    cost_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    sale_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[str] = mapped_column(String(1000), default="")

    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)

    movements: Mapped[list["StockMovement"]] = relationship(back_populates="stock_item", cascade="all, delete-orphan")


class StockMovement(Base):
    """Auditoria de toda entrada/saída/ajuste de estoque. A quantidade do
    StockItem nunca é alterada sem gravar aqui o motivo — inclusive as baixas
    automáticas por fechamento de Ordem de Serviço (ver app/api/work_order_routes.py)."""

    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    stock_item_id: Mapped[int] = mapped_column(ForeignKey("stock_items.id", ondelete="CASCADE"), index=True)
    work_order_id: Mapped[int | None] = mapped_column(ForeignKey("work_orders.id", ondelete="SET NULL"), nullable=True)

    type: Mapped[StockMovementType] = mapped_column(Enum(StockMovementType, native_enum=False, length=20))
    quantity: Mapped[int] = mapped_column(Integer)  # sempre positivo; `type` indica a direção
    reason: Mapped[str] = mapped_column(String(255), default="")
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)

    stock_item: Mapped["StockItem"] = relationship(back_populates="movements")
