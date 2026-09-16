from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_db, require_permission
from app.core.sessions import SessionData
from app.models.notification import NotificationLog
from app.models.notification_queue import NotificationRequest
from app.schemas.notification import NotificationLogResponse, RevisionCheckResult
from app.schemas.notification_queue import NotificationQueueEntryResponse, ProcessQueueResult
from app.services.notifications import check_upcoming_revisions, process_notification_queue

notification_router = APIRouter()


@notification_router.get("/notifications", response_model=list[NotificationLogResponse])
def list_notifications(
    user: SessionData = Depends(require_permission("notifications.manage")),
    db: Session = Depends(get_tenant_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    rows = (
        db.query(NotificationLog)
        .filter(NotificationLog.company_id == user.company_id)
        .order_by(NotificationLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return rows


@notification_router.post("/notifications/check-revisions", response_model=RevisionCheckResult)
def trigger_revision_check(
    user: SessionData = Depends(require_permission("notifications.manage")),
    db: Session = Depends(get_tenant_db),
):
    """Dispara manualmente a varredura de revisões prestes a vencer (o mesmo
    processo que, em produção, roda por um cron/worker agendado)."""
    logs = check_upcoming_revisions(db, user.company_id)
    return RevisionCheckResult(reminders_sent=len(logs) // 2, logs=logs)


@notification_router.get("/notifications/queue", response_model=list[NotificationQueueEntryResponse])
def list_notification_queue(
    user: SessionData = Depends(require_permission("notifications.manage")),
    db: Session = Depends(get_tenant_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """Notificações que falharam no envio imediato e estão aguardando (ou
    esgotaram) o reenvio — ver app/services/notifications.py (FASE 11)."""
    rows = (
        db.query(NotificationRequest)
        .filter(NotificationRequest.company_id == user.company_id)
        .order_by(NotificationRequest.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return rows


@notification_router.post("/notifications/process-queue", response_model=ProcessQueueResult)
def process_notification_queue_route(
    user: SessionData = Depends(require_permission("notifications.manage")),
    db: Session = Depends(get_tenant_db),
):
    """Dispara manualmente o reprocessamento da fila de retry (o mesmo
    processo que, em produção, roda por um cron/worker agendado)."""
    summary = process_notification_queue(db, user.company_id)
    return ProcessQueueResult(**summary)
