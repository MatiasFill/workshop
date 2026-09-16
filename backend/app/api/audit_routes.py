from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_db, require_permission
from app.core.sessions import SessionData
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse

audit_router = APIRouter()

# Somente leitura de propósito: a trilha de auditoria é gravada exclusivamente
# por app/services/audit.py a partir das próprias rotas de negócio — não há
# criação/edição/remoção aqui.


@audit_router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    user: SessionData = Depends(require_permission("audit.read")),
    db: Session = Depends(get_tenant_db),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(AuditLog).filter(AuditLog.company_id == user.company_id)
    if action is not None:
        query = query.filter(AuditLog.action == action)
    if entity_type is not None:
        query = query.filter(AuditLog.entity_type == entity_type)
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)

    return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
