"""
Serviço de notificações. FASE 4/5: comprovante de OS por e-mail e WhatsApp
(valor, material usado, data do serviço, data da próxima revisão) e alerta
de "sua revisão está prestes a vencer" — envio imediato e síncrono.

FASE 11 acrescenta retry/backoff com idempotência: quando um envio imediato
FALHA (erro de SMTP/API, não "sem configuração"), a notificação é
automaticamente enfileirada em NotificationRequest para nova tentativa —
nunca duplicada, graças à `idempotency_key` única por empresa. Ver
`process_notification_queue`, pensado para ser chamado por um cron/worker
(ou manualmente via POST /api/notifications/process-queue).

Resiliência: se SMTP ou a API de WhatsApp não estiverem configurados (ver
Settings), o envio é apenas marcado como SKIPPED no NotificationLog — nunca
lança exceção para quem chamou, e nunca entra na fila de retry (retentar
não resolveria a falta de configuração).
"""
from __future__ import annotations

import smtplib
from datetime import date, datetime, timedelta
from email.mime.text import MIMEText

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.customer import Customer
from app.models.notification import (
    NotificationChannel,
    NotificationLog,
    NotificationStatus,
    NotificationType,
)
from app.models.notification_queue import NotificationRequest, NotificationRequestStatus
from app.models.work_order import WorkOrder, WorkOrderItem, WorkOrderItemKind, WorkOrderStatus

MAX_RETRY_ATTEMPTS = 5


def _log(
    db: Session,
    company_id: int,
    customer_id: int | None,
    work_order_id: int | None,
    channel: NotificationChannel,
    type_: NotificationType,
    status: NotificationStatus,
    detail: str,
) -> NotificationLog:
    entry = NotificationLog(
        company_id=company_id,
        customer_id=customer_id,
        work_order_id=work_order_id,
        channel=channel,
        type=type_,
        status=status,
        detail=detail[:500],
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def _send_email(to_address: str, subject: str, body: str) -> tuple[NotificationStatus, str]:
    if not to_address:
        return NotificationStatus.SKIPPED, "Cliente sem e-mail cadastrado."
    if not settings.notifications_enabled_email:
        return NotificationStatus.SKIPPED, "SMTP não configurado (defina SMTP_HOST/SMTP_USER/SMTP_PASSWORD)."
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_address
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, [to_address], msg.as_string())
        return NotificationStatus.SENT, "Enviado via SMTP."
    except Exception as exc:  # pragma: no cover — depende de um servidor SMTP real
        return NotificationStatus.FAILED, f"Erro ao enviar e-mail: {exc}"


def _send_whatsapp(to_phone: str, message: str) -> tuple[NotificationStatus, str]:
    if not to_phone:
        return NotificationStatus.SKIPPED, "Cliente sem telefone cadastrado."
    if not settings.notifications_enabled_whatsapp:
        return NotificationStatus.SKIPPED, "API de WhatsApp não configurada (defina WHATSAPP_API_URL/WHATSAPP_API_TOKEN)."
    try:
        response = httpx.post(
            settings.WHATSAPP_API_URL,
            headers={"Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}"},
            json={"from": settings.WHATSAPP_FROM_NUMBER, "to": to_phone, "message": message},
            timeout=10,
        )
        response.raise_for_status()
        return NotificationStatus.SENT, "Enviado via API de WhatsApp."
    except Exception as exc:  # pragma: no cover — depende de um provedor de WhatsApp real
        return NotificationStatus.FAILED, f"Erro ao enviar WhatsApp: {exc}"


def _next_backoff(attempts: int) -> datetime:
    """Backoff exponencial em minutos (1, 2, 4, 8, 16...), com teto de 60min
    para não deixar o worker esperando horas entre tentativas."""
    minutes = min(60, 2**attempts)
    return datetime.utcnow() + timedelta(minutes=minutes)


def _enqueue_retry(
    db: Session,
    *,
    company_id: int,
    idempotency_key: str,
    channel: NotificationChannel,
    type_: NotificationType,
    customer_id: int | None,
    work_order_id: int | None,
    subject: str,
    message: str,
    last_error: str,
) -> NotificationRequest:
    """Idempotente: se já existe uma entrada pendente/em retry para essa
    chave, não duplica — só atualiza o erro mais recente."""
    existing = (
        db.query(NotificationRequest)
        .filter(
            NotificationRequest.company_id == company_id,
            NotificationRequest.idempotency_key == idempotency_key,
        )
        .first()
    )
    if existing:
        if existing.status in (NotificationRequestStatus.PENDING, NotificationRequestStatus.FAILED):
            existing.last_error = last_error[:500]
            db.commit()
        return existing

    entry = NotificationRequest(
        company_id=company_id,
        idempotency_key=idempotency_key,
        channel=channel,
        type=type_,
        customer_id=customer_id,
        work_order_id=work_order_id,
        subject=subject[:255],
        message=message[:2000],
        status=NotificationRequestStatus.PENDING,
        attempts=0,
        max_attempts=MAX_RETRY_ATTEMPTS,
        next_attempt_at=_next_backoff(0),
        last_error=last_error[:500],
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def process_notification_queue(db: Session, company_id: int, limit: int = 50) -> dict:
    """Puxa o próximo lote de notificações pendentes/em retry cujo horário
    já chegou, tenta reenviar, e atualiza status/tentativas/backoff. Cada
    tentativa também grava um NotificationLog, como no envio imediato.

    Sem agendador embutido neste scaffold (mesmo padrão de
    check_upcoming_revisions): pensado para ser chamado por um cron/worker
    externo, ou manualmente via POST /api/notifications/process-queue.
    """
    now = datetime.utcnow()
    due = (
        db.query(NotificationRequest)
        .filter(
            NotificationRequest.company_id == company_id,
            NotificationRequest.status.in_([NotificationRequestStatus.PENDING, NotificationRequestStatus.FAILED]),
            NotificationRequest.next_attempt_at <= now,
        )
        .order_by(NotificationRequest.next_attempt_at.asc())
        .limit(limit)
        .all()
    )

    summary = {"sent": 0, "failed_retry": 0, "given_up": 0}
    for req in due:
        customer = db.query(Customer).filter(Customer.id == req.customer_id).first() if req.customer_id else None
        if not customer:
            req.status = NotificationRequestStatus.GIVEN_UP
            req.last_error = "Cliente não encontrado mais."
            summary["given_up"] += 1
            db.commit()
            continue

        if req.channel == NotificationChannel.EMAIL:
            status, detail = _send_email(customer.email, req.subject, req.message)
        else:
            status, detail = _send_whatsapp(customer.phone, req.message)

        req.attempts += 1
        if status == NotificationStatus.SENT:
            req.status = NotificationRequestStatus.SENT
            summary["sent"] += 1
        elif status == NotificationStatus.SKIPPED:
            # perdeu a configuração/contato entre o enfileiramento e agora —
            # retentar não ajudaria, então encerra sem contar como sucesso nem falha.
            req.status = NotificationRequestStatus.SKIPPED
        elif req.attempts >= req.max_attempts:
            req.status = NotificationRequestStatus.GIVEN_UP
            req.last_error = detail[:500]
            summary["given_up"] += 1
        else:
            req.status = NotificationRequestStatus.FAILED
            req.next_attempt_at = _next_backoff(req.attempts)
            req.last_error = detail[:500]
            summary["failed_retry"] += 1

        _log(db, company_id, req.customer_id, req.work_order_id, req.channel, req.type, status, detail)
        db.commit()

    return summary


def notify_work_order_receipt(db: Session, work_order: WorkOrder) -> list[NotificationLog]:
    """Envia o comprovante da OS finalizada por e-mail e WhatsApp: valor
    total, material usado, data do serviço e data da próxima revisão."""
    customer = db.query(Customer).filter(Customer.id == work_order.customer_id).first()
    if not customer:
        return []

    items = db.query(WorkOrderItem).filter(WorkOrderItem.work_order_id == work_order.id).all()
    parts = [i for i in items if i.kind == WorkOrderItemKind.PART]
    materials = ", ".join(f"{i.description} (x{i.quantity})" for i in parts) or "nenhum material avulso"

    items_total = sum(float(i.quantity) * float(i.unit_price) for i in items)
    total = float(work_order.labor_value) + items_total - float(work_order.discount_value)

    service_date = (work_order.closed_at or datetime.utcnow()).strftime("%d/%m/%Y")
    next_revision = (
        work_order.next_revision_date.strftime("%d/%m/%Y") if work_order.next_revision_date else "não definida"
    )

    message = (
        f"Olá {customer.name}, sua Ordem de Serviço #{work_order.id} foi concluída em {service_date}.\n"
        f"Valor total: R$ {total:.2f}\n"
        f"Material usado: {materials}\n"
        f"Próxima revisão recomendada: {next_revision}"
    )

    logs: list[NotificationLog] = []

    email_status, email_detail = _send_email(customer.email, f"Comprovante da OS #{work_order.id}", message)
    logs.append(
        _log(
            db, work_order.company_id, customer.id, work_order.id,
            NotificationChannel.EMAIL, NotificationType.WORK_ORDER_RECEIPT, email_status, email_detail,
        )
    )
    if email_status == NotificationStatus.FAILED:
        _enqueue_retry(
            db, company_id=work_order.company_id, idempotency_key=f"work_order:{work_order.id}:receipt:email",
            channel=NotificationChannel.EMAIL, type_=NotificationType.WORK_ORDER_RECEIPT,
            customer_id=customer.id, work_order_id=work_order.id,
            subject=f"Comprovante da OS #{work_order.id}", message=message, last_error=email_detail,
        )

    wa_status, wa_detail = _send_whatsapp(customer.phone, message)
    logs.append(
        _log(
            db, work_order.company_id, customer.id, work_order.id,
            NotificationChannel.WHATSAPP, NotificationType.WORK_ORDER_RECEIPT, wa_status, wa_detail,
        )
    )
    if wa_status == NotificationStatus.FAILED:
        _enqueue_retry(
            db, company_id=work_order.company_id, idempotency_key=f"work_order:{work_order.id}:receipt:whatsapp",
            channel=NotificationChannel.WHATSAPP, type_=NotificationType.WORK_ORDER_RECEIPT,
            customer_id=customer.id, work_order_id=work_order.id,
            subject="", message=message, last_error=wa_detail,
        )

    return logs


def check_upcoming_revisions(db: Session, company_id: int, days_ahead: int | None = None) -> list[NotificationLog]:
    """Varre as OS concluídas da empresa com `next_revision_date` dentro da
    janela configurada (REVISION_REMINDER_DAYS_AHEAD por padrão) e ainda não
    lembradas, envia o alerta "sua revisão está prestes a vencer" por e-mail
    e WhatsApp, e marca `revision_reminder_sent_at` para não duplicar.

    Não há agendador embutido neste scaffold: este método é pensado para ser
    chamado por um cron/worker externo (ou manualmente via
    POST /api/notifications/check-revisions, ver notification_routes.py).
    """
    window = days_ahead if days_ahead is not None else settings.REVISION_REMINDER_DAYS_AHEAD
    today = date.today()
    limit_date = today + timedelta(days=window)

    candidates = (
        db.query(WorkOrder)
        .filter(
            WorkOrder.company_id == company_id,
            WorkOrder.status == WorkOrderStatus.DONE,
            WorkOrder.next_revision_date.isnot(None),
            WorkOrder.next_revision_date >= today,
            WorkOrder.next_revision_date <= limit_date,
            WorkOrder.revision_reminder_sent_at.is_(None),
        )
        .all()
    )

    logs: list[NotificationLog] = []
    for wo in candidates:
        customer = db.query(Customer).filter(Customer.id == wo.customer_id).first()
        if not customer:
            continue

        next_revision = wo.next_revision_date.strftime("%d/%m/%Y")
        message = (
            f"Olá {customer.name}, sua revisão está prestes a vencer "
            f"(recomendada para {next_revision}). Entre em contato para agendar."
        )

        email_status, email_detail = _send_email(customer.email, "Sua revisão está prestes a vencer", message)
        logs.append(
            _log(
                db, company_id, customer.id, wo.id,
                NotificationChannel.EMAIL, NotificationType.REVISION_REMINDER, email_status, email_detail,
            )
        )
        if email_status == NotificationStatus.FAILED:
            _enqueue_retry(
                db, company_id=company_id, idempotency_key=f"work_order:{wo.id}:revision_reminder:email",
                channel=NotificationChannel.EMAIL, type_=NotificationType.REVISION_REMINDER,
                customer_id=customer.id, work_order_id=wo.id,
                subject="Sua revisão está prestes a vencer", message=message, last_error=email_detail,
            )

        wa_status, wa_detail = _send_whatsapp(customer.phone, message)
        logs.append(
            _log(
                db, company_id, customer.id, wo.id,
                NotificationChannel.WHATSAPP, NotificationType.REVISION_REMINDER, wa_status, wa_detail,
            )
        )
        if wa_status == NotificationStatus.FAILED:
            _enqueue_retry(
                db, company_id=company_id, idempotency_key=f"work_order:{wo.id}:revision_reminder:whatsapp",
                channel=NotificationChannel.WHATSAPP, type_=NotificationType.REVISION_REMINDER,
                customer_id=customer.id, work_order_id=wo.id,
                subject="", message=message, last_error=wa_detail,
            )

        wo.revision_reminder_sent_at = datetime.utcnow()
        db.commit()

    return logs
