from datetime import datetime
from app.core.clock import utcnow_naive

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

_DOCUMENT_NOT_EMPTY = text("document != ''")


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        # CPF/CNPJ é opcional (cliente pode ser cadastrado só com nome/telefone
        # na recepção). A unicidade só vale quando o documento é informado —
        # por isso é um índice único PARCIAL (WHERE document != ''), e não uma
        # UniqueConstraint normal: uma constraint comum trataria "" como um
        # valor igual a qualquer outro "" e quebraria no segundo cliente sem
        # documento cadastrado na mesma empresa.
        Index(
            "uq_customers_company_document",
            "company_id",
            "document",
            unique=True,
            postgresql_where=_DOCUMENT_NOT_EMPTY,
            sqlite_where=_DOCUMENT_NOT_EMPTY,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(255))
    document: Mapped[str] = mapped_column(String(20), default="")  # CPF ou CNPJ, dígitos
    phone: Mapped[str] = mapped_column(String(20), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    address: Mapped[str] = mapped_column(String(500), default="")
    notes: Mapped[str] = mapped_column(String(1000), default="")

    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)

    # FASE 9 (LGPD, art. 18 — direito de exclusão/anonimização): quando
    # anonimizado, os campos de identificação pessoal acima são
    # sobrescritos por app/services/lgpd.py — os registros de negócio
    # ligados a este cliente (veículos, OS, financeiro) são preservados
    # para cumprir prazos legais de guarda contábil/fiscal.
    is_anonymized: Mapped[bool] = mapped_column(default=False)
    anonymized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="customer", cascade="all, delete-orphan")


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        # Placa única por empresa (não globalmente: mesma placa pode, em teoria,
        # existir em bases de clientes diferentes por erro de digitação alheio
        # e isso não deve travar o cadastro de outra empresa).
        UniqueConstraint("company_id", "plate", name="uq_vehicles_company_plate"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)

    plate: Mapped[str] = mapped_column(String(10))  # normalizada em maiúsculas, sem hífen
    brand: Mapped[str] = mapped_column(String(100), default="")
    model: Mapped[str] = mapped_column(String(100), default="")
    year: Mapped[int | None] = mapped_column(nullable=True)
    color: Mapped[str] = mapped_column(String(50), default="")
    km: Mapped[int | None] = mapped_column(nullable=True)
    notes: Mapped[str] = mapped_column(String(1000), default="")

    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)

    customer: Mapped["Customer"] = relationship(back_populates="vehicles")
