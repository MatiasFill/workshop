"""
Serviço de auditoria (FASE 8). Uso: chamar `log_action` depois que a ação de
negócio principal já foi commitada — assim, se a auditoria falhar por algum
motivo, isso não desfaz nem impede a ação de negócio (e vice-versa: um erro
posterior na função que chamou não reverte um log que já foi gravado).
"""
from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log_action(
    db: Session,
    *,
    company_id: int,
    user_id: int | None,
    action: str,
    entity_type: str = "",
    entity_id: int | None = None,
    detail: str = "",
    ip_address: str = "",
) -> AuditLog:
    entry = AuditLog(
        company_id=company_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail[:1000],
        ip_address=ip_address[:45],
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
