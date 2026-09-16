"""
Serviço de LGPD (FASE 9): direito de acesso/portabilidade (art. 15/18) via
exportação de todos os dados ligados a um cliente, e direito de exclusão/
anonimização (art. 18) via `anonymize_customer`.

Anonimizar não apaga o cliente nem os registros de negócio ligados a ele
(veículos, agendamentos, ordens de serviço, lançamentos financeiros) — só
sobrescreve os campos de identificação pessoal do próprio `Customer`. Os
registros de negócio são preservados porque frequentemente há prazo legal
de guarda contábil/fiscal (Código Civil, legislação tributária) que a LGPD
não anula; o próprio art. 16 da LGPD permite manter dados pessoais além do
pedido de eliminação quando necessário para cumprimento de obrigação legal.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.customer import Customer, Vehicle
from app.models.finance import FinanceEntry
from app.models.notification import NotificationLog
from app.models.work_order import WorkOrder, WorkOrderItem

ANONYMIZED_NAME = "Cliente anonimizado"


def export_customer_data(db: Session, company_id: int, customer_id: int) -> dict | None:
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.company_id == company_id)
        .first()
    )
    if not customer:
        return None

    vehicles = db.query(Vehicle).filter(Vehicle.customer_id == customer.id).all()
    appointments = db.query(Appointment).filter(Appointment.customer_id == customer.id).all()
    work_orders = db.query(WorkOrder).filter(WorkOrder.customer_id == customer.id).all()
    finance_entries = db.query(FinanceEntry).filter(FinanceEntry.customer_id == customer.id).all()
    notifications = db.query(NotificationLog).filter(NotificationLog.customer_id == customer.id).all()

    work_order_bundles = []
    for wo in work_orders:
        items = db.query(WorkOrderItem).filter(WorkOrderItem.work_order_id == wo.id).all()
        work_order_bundles.append(
            {
                "id": wo.id,
                "status": wo.status.value,
                "total_value": float(wo.labor_value)
                + sum(float(i.quantity) * float(i.unit_price) for i in items)
                - float(wo.discount_value),
                "created_at": wo.created_at,
                "closed_at": wo.closed_at,
                "items": [
                    {"description": i.description, "quantity": i.quantity, "unit_price": float(i.unit_price)}
                    for i in items
                ],
            }
        )

    return {
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "document": customer.document,
            "phone": customer.phone,
            "email": customer.email,
            "address": customer.address,
            "notes": customer.notes,
            "is_active": customer.is_active,
            "is_anonymized": customer.is_anonymized,
            "created_at": customer.created_at,
        },
        "vehicles": [
            {
                "id": v.id, "plate": v.plate, "brand": v.brand, "model": v.model,
                "year": v.year, "color": v.color,
            }
            for v in vehicles
        ],
        "appointments": [
            {
                "id": a.id, "scheduled_at": a.scheduled_at, "status": a.status.value,
                "service_type": a.service_type,
            }
            for a in appointments
        ],
        "work_orders": work_order_bundles,
        "finance_entries": [
            {
                "id": f.id, "type": f.type.value, "status": f.status.value,
                "amount": float(f.amount), "due_date": f.due_date, "paid_amount": float(f.paid_amount),
            }
            for f in finance_entries
        ],
        "notifications": [
            {"channel": n.channel.value, "type": n.type.value, "status": n.status.value, "created_at": n.created_at}
            for n in notifications
        ],
        "exported_at": datetime.utcnow(),
    }


def anonymize_customer(db: Session, company_id: int, customer_id: int) -> Customer | None:
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.company_id == company_id)
        .first()
    )
    if not customer:
        return None

    customer.name = ANONYMIZED_NAME
    customer.document = ""
    customer.phone = ""
    customer.email = ""
    customer.address = ""
    customer.notes = ""
    customer.is_active = False
    customer.is_anonymized = True
    customer.anonymized_at = datetime.utcnow()

    db.commit()
    db.refresh(customer)
    return customer
