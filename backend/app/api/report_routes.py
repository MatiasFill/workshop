from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_db, require_permission
from app.core.sessions import SessionData
from app.models.customer import Customer
from app.models.finance import CashMovement, CashMovementType, CashSession, CashSessionStatus, FinanceEntry, FinanceEntryStatus, FinanceEntryType
from app.models.stock import StockItem
from app.models.work_order import WorkOrder, WorkOrderItem, WorkOrderItemKind, WorkOrderStatus
from app.schemas.report import DashboardReport, MonthlyPoint

report_router = APIRouter()


def _month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _work_order_financials(db: Session, wo: WorkOrder) -> tuple[float, float]:
    """Retorna (receita, lucro) de uma OS concluída.

    Lucro é uma aproximação didática deste scaffold: receita menos o custo
    das peças usadas (quantidade x custo atual do item de estoque, ver
    StockItem.cost_price) — mão de obra é tratada como 100% de margem, já que
    o sistema não tem folha de pagamento/custo de mecânico neste momento.
    """
    items = db.query(WorkOrderItem).filter(WorkOrderItem.work_order_id == wo.id).all()
    revenue = float(wo.labor_value) - float(wo.discount_value)
    parts_cost = 0.0
    for item in items:
        item_revenue = float(item.quantity) * float(item.unit_price)
        revenue += item_revenue
        if item.kind == WorkOrderItemKind.PART and item.stock_item_id is not None:
            stock_item = db.query(StockItem).filter(StockItem.id == item.stock_item_id).first()
            if stock_item:
                parts_cost += float(item.quantity) * float(stock_item.cost_price)
    return revenue, revenue - parts_cost


@report_router.get("/reports/dashboard", response_model=DashboardReport)
def get_dashboard(
    user: SessionData = Depends(require_permission("reports.read")),
    db: Session = Depends(get_tenant_db),
    months: int = Query(default=6, ge=1, le=24, description="Quantos meses incluir na série de comparação"),
):
    # --- Estoque -----------------------------------------------------
    stock_items = db.query(StockItem).filter(StockItem.company_id == user.company_id, StockItem.is_active.is_(True)).all()
    stock_value = sum(float(i.quantity) * float(i.cost_price) for i in stock_items)
    stock_critical_items = sum(1 for i in stock_items if i.quantity <= i.min_quantity)

    # --- Ordens de serviço -------------------------------------------
    open_work_orders = (
        db.query(func.count(WorkOrder.id))
        .filter(
            WorkOrder.company_id == user.company_id,
            WorkOrder.status.notin_([WorkOrderStatus.DONE, WorkOrderStatus.CANCELLED]),
        )
        .scalar()
        or 0
    )

    # --- Clientes ------------------------------------------------------
    customers_total = (
        db.query(func.count(Customer.id))
        .filter(Customer.company_id == user.company_id, Customer.is_active.is_(True))
        .scalar()
        or 0
    )
    today = date.today()
    customers_new_this_month = (
        db.query(func.count(Customer.id))
        .filter(
            Customer.company_id == user.company_id,
            extract("year", Customer.created_at) == today.year,
            extract("month", Customer.created_at) == today.month,
        )
        .scalar()
        or 0
    )

    # --- Financeiro (série mês a mês, calculada a partir das OS concluídas) ---
    closed_orders = (
        db.query(WorkOrder)
        .filter(WorkOrder.company_id == user.company_id, WorkOrder.status == WorkOrderStatus.DONE)
        .all()
    )

    by_month: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0])  # revenue, profit, count
    for wo in closed_orders:
        if not wo.closed_at:
            continue
        key = _month_key(wo.closed_at.date())
        revenue, profit = _work_order_financials(db, wo)
        by_month[key][0] += revenue
        by_month[key][1] += profit
        by_month[key][2] += 1

    sorted_keys = sorted(by_month.keys())[-months:]
    monthly_series = [
        MonthlyPoint(
            month=key,
            revenue=round(by_month[key][0], 2),
            profit=round(by_month[key][1], 2),
            work_orders_closed=int(by_month[key][2]),
        )
        for key in sorted_keys
    ]

    this_month_key = _month_key(today)
    last_month_date = date(today.year - 1, 12, 1) if today.month == 1 else date(today.year, today.month - 1, 1)
    last_month_key = _month_key(last_month_date)

    this_month = by_month.get(this_month_key, [0.0, 0.0, 0])
    last_month = by_month.get(last_month_key, [0.0, 0.0, 0])

    # --- Financeiro (FASE 6) -------------------------------------------
    open_entries = (
        db.query(FinanceEntry)
        .filter(FinanceEntry.company_id == user.company_id, FinanceEntry.status == FinanceEntryStatus.PENDING)
        .all()
    )
    receivables_pending = sum(
        float(e.amount) - float(e.paid_amount) for e in open_entries if e.type == FinanceEntryType.RECEIVABLE
    )
    payables_pending = sum(
        float(e.amount) - float(e.paid_amount) for e in open_entries if e.type == FinanceEntryType.PAYABLE
    )

    open_cash_session = (
        db.query(CashSession)
        .filter(CashSession.company_id == user.company_id, CashSession.status == CashSessionStatus.OPEN)
        .first()
    )
    cash_balance = None
    if open_cash_session:
        movements = db.query(CashMovement).filter(CashMovement.cash_session_id == open_cash_session.id).all()
        cash_balance = float(open_cash_session.opening_amount)
        for m in movements:
            cash_balance += float(m.amount) if m.type == CashMovementType.IN else -float(m.amount)
        cash_balance = round(cash_balance, 2)

    return DashboardReport(
        stock_value=round(stock_value, 2),
        stock_critical_items=stock_critical_items,
        open_work_orders=int(open_work_orders),
        customers_total=int(customers_total),
        customers_new_this_month=int(customers_new_this_month),
        revenue_this_month=round(this_month[0], 2),
        profit_this_month=round(this_month[1], 2),
        revenue_last_month=round(last_month[0], 2),
        profit_last_month=round(last_month[1], 2),
        receivables_pending=round(receivables_pending, 2),
        payables_pending=round(payables_pending, 2),
        cash_balance=cash_balance,
        monthly_series=monthly_series,
    )
