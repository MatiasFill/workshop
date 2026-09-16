from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_db, require_permission
from app.core.sessions import SessionData
from app.schemas.retention import AnonymizeInactiveResult, PurgeNotificationsResult, RetentionCandidate
from app.services.audit import log_action
from app.services.lgpd import anonymize_customer
from app.services.retention import (
    find_customers_eligible_for_anonymization,
    last_activity_at,
    purge_old_notification_logs,
)

retention_router = APIRouter()

# Mesma lógica de app/api/notification_routes.py (check-revisions): sem
# agendador embutido neste scaffold, estas rotas existem para serem
# chamadas por um cron/worker externo ou manualmente por um ADMIN/MANAGER.


@retention_router.get("/retention/candidates", response_model=list[RetentionCandidate])
def list_retention_candidates(
    user: SessionData = Depends(require_permission("lgpd.manage")),
    db: Session = Depends(get_tenant_db),
):
    """Clientes inativos há muitos anos e sem financeiro em aberto —
    candidatos a anonimização automática por minimização de dados. Só
    lista; não altera nada (ver POST /retention/anonymize-inactive)."""
    customers = find_customers_eligible_for_anonymization(db, user.company_id)
    return [
        RetentionCandidate(
            id=c.id, name=c.name, last_activity_at=last_activity_at(db, c), created_at=c.created_at,
        )
        for c in customers
    ]


@retention_router.post("/retention/purge-notifications", response_model=PurgeNotificationsResult)
def purge_notifications_route(
    user: SessionData = Depends(require_permission("lgpd.manage")),
    db: Session = Depends(get_tenant_db),
):
    """Apaga o log de notificações mais antigo que RETENTION_NOTIFICATION_LOGS_DAYS."""
    deleted = purge_old_notification_logs(db, user.company_id)
    log_action(
        db, company_id=user.company_id, user_id=user.user_id, action="retention.purge_notifications",
        detail=f"{deleted} registro(s) apagado(s)",
    )
    return PurgeNotificationsResult(deleted_count=deleted)


@retention_router.post("/retention/anonymize-inactive", response_model=AnonymizeInactiveResult)
def anonymize_inactive_route(
    user: SessionData = Depends(require_permission("lgpd.manage")),
    db: Session = Depends(get_tenant_db),
):
    """Anonimiza em massa todo cliente que aparece em GET /retention/candidates."""
    candidates = find_customers_eligible_for_anonymization(db, user.company_id)
    anonymized_ids: list[int] = []
    for customer in candidates:
        anonymize_customer(db, user.company_id, customer.id)
        log_action(
            db, company_id=user.company_id, user_id=user.user_id, action="customer.anonymize",
            entity_type="customer", entity_id=customer.id,
            detail="Anonimização automática por inatividade (política de retenção)",
        )
        anonymized_ids.append(customer.id)

    return AnonymizeInactiveResult(anonymized_count=len(anonymized_ids), customer_ids=anonymized_ids)
