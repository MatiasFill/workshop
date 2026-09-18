"""
Serviço de retenção de dados (FASE 10) — complementa a FASE 9 (LGPD) com o
princípio de minimização (art. 6º, VII): não reter dado pessoal além do
necessário para a finalidade do tratamento.

Sem agendador embutido neste scaffold (mesmo padrão de
check_upcoming_revisions em app/services/notifications.py) — os métodos
aqui são pensados para ser chamados por um cron/worker externo, ou
manualmente via os endpoints em app/api/retention_routes.py.
"""
from datetime import date, datetime, timedelta
from app.core.clock import utcnow_naive

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.appointment import Appointment
from app.models.customer import Customer
from app.models.finance import FinanceEntry, FinanceEntryStatus
from app.models.notification import NotificationLog
from app.models.work_order import WorkOrder


def purge_old_notification_logs(db: Session, company_id: int, days: int | None = None) -> int:
    """Apaga `NotificationLog` mais antigos que `days` (padrão
    RETENTION_NOTIFICATION_LOGS_DAYS). São registros puramente operacionais
    — log de tentativa de envio de comprovante/lembrete — sem valor de
    guarda contábil ou fiscal, e carregam `customer_id`: quanto antes
    minimizados, melhor."""
    window = days if days is not None else settings.RETENTION_NOTIFICATION_LOGS_DAYS
    cutoff = utcnow_naive() - timedelta(days=window)
    deleted = (
        db.query(NotificationLog)
        .filter(NotificationLog.company_id == company_id, NotificationLog.created_at < cutoff)
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted


def last_activity_at(db: Session, customer: Customer) -> datetime | None:
    """Data do agendamento ou OS mais recente deste cliente (o que for mais
    novo). `None` se o cliente nunca teve nenhum dos dois."""
    dates = []
    last_appt = (
        db.query(func.max(Appointment.scheduled_at)).filter(Appointment.customer_id == customer.id).scalar()
    )
    if last_appt:
        dates.append(last_appt)
    last_wo = db.query(func.max(WorkOrder.created_at)).filter(WorkOrder.customer_id == customer.id).scalar()
    if last_wo:
        dates.append(last_wo)
    return max(dates) if dates else None


def find_customers_eligible_for_anonymization(
    db: Session, company_id: int, years: int | None = None
) -> list[Customer]:
    """Clientes ainda não anonimizados, sem nenhuma atividade (agendamento
    ou OS) nos últimos `years` (padrão RETENTION_INACTIVE_CUSTOMER_YEARS) e
    sem lançamento financeiro em aberto — minimização de dados: não há
    motivo para reter o cadastro pessoal de alguém que não é cliente ativo
    e não tem nenhuma pendência."""
    window_years = years if years is not None else settings.RETENTION_INACTIVE_CUSTOMER_YEARS
    today = date.today()
    cutoff = today.replace(year=today.year - window_years)

    candidates: list[Customer] = []
    customers = (
        db.query(Customer)
        .filter(Customer.company_id == company_id, Customer.is_anonymized.is_(False))
        .all()
    )
    for customer in customers:
        activity = last_activity_at(db, customer)
        reference_date = activity.date() if activity else customer.created_at.date()
        if reference_date >= cutoff:
            continue  # teve atividade (ou foi cadastrado) dentro da janela — não é candidato

        has_open_finance = (
            db.query(FinanceEntry)
            .filter(FinanceEntry.customer_id == customer.id, FinanceEntry.status == FinanceEntryStatus.PENDING)
            .first()
        )
        if has_open_finance:
            continue  # ainda há pendência financeira ligada a este cliente

        candidates.append(customer)

    return candidates
