from sqlalchemy import ForeignKey, String, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.clock import utcnow_naive
from app.db.session import Base

class MemoryEntry(Base):
    __tablename__ = "memory_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Escopo por empresa: sem isso, uma resposta gravada por uma empresa
    # poderia ser servida para outra (risco já apontado na revisão de
    # segurança como "memory poisoning" — isto fecha metade do problema;
    # a outra metade é a autenticação/RBAC em cima do endpoint).
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    question_hash: Mapped[str] = mapped_column(String(64), index=True)
    question: Mapped[str] = mapped_column(Text)
    context_hash: Mapped[str] = mapped_column(String(64), index=True, default="")
    answer: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)
