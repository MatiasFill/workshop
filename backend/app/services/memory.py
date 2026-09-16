import hashlib
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.memory import MemoryEntry
from app.core.config import settings

def _hash(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()

def lookup(db: Session, company_id: int, question: str, context: str = ""):
    qh = _hash(question)
    ch = _hash(context)
    item = db.scalar(select(MemoryEntry).where(
        MemoryEntry.company_id == company_id,
        MemoryEntry.question_hash == qh,
        MemoryEntry.context_hash == ch
    ))
    if not item:
        return None
    if datetime.utcnow() - item.created_at > timedelta(seconds=settings.MEMORY_TTL_SECONDS):
        return None
    return item

def save(db: Session, company_id: int, question: str, answer: str, context: str = ""):
    item = MemoryEntry(
        company_id=company_id,
        question_hash=_hash(question),
        question=question,
        context_hash=_hash(context),
        answer=answer
    )
    db.add(item)
    db.commit()
    return item
