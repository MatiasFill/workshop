from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_db, require_permission
from app.core.sessions import SessionData
from app.models.customer import Customer
from app.models.finance import (
    CashMovement,
    CashMovementType,
    CashSession,
    CashSessionStatus,
    FinanceEntry,
    FinanceEntryStatus,
    FinanceEntryType,
)
from app.schemas.finance import (
    FinanceEntryCreate,
    FinanceEntryPayRequest,
    FinanceEntryResponse,
    FinanceEntryUpdate,
)
from app.services.audit import log_action

finance_router = APIRouter()

# Mesmo princípio das demais rotas: company_id nunca vem do corpo da
# requisição — sempre da sessão autenticada, resolvida por get_tenant_db.


def _effective_status(entry: FinanceEntry) -> FinanceEntryStatus:
    """PENDING vencida vira OVERDUE só na leitura — não é um estado
    persistido à parte, para não precisar de um job batendo o banco todo
    dia só para atualizar status."""
    if entry.status == FinanceEntryStatus.PENDING and entry.due_date < date.today():
        return FinanceEntryStatus.OVERDUE
    return entry.status


def _to_response(db: Session, entry: FinanceEntry) -> FinanceEntryResponse:
    customer = db.query(Customer).filter(Customer.id == entry.customer_id).first() if entry.customer_id else None
    return FinanceEntryResponse(
        id=entry.id,
        type=entry.type,
        status=_effective_status(entry),
        category=entry.category,
        description=entry.description,
        amount=float(entry.amount),
        due_date=entry.due_date,
        paid_amount=float(entry.paid_amount),
        remaining_amount=round(float(entry.amount) - float(entry.paid_amount), 2),
        paid_at=entry.paid_at,
        customer_id=entry.customer_id,
        customer_name=customer.name if customer else "",
        work_order_id=entry.work_order_id,
        created_at=entry.created_at,
    )


def _get_entry_or_404(db: Session, company_id: int, entry_id: int) -> FinanceEntry:
    entry = (
        db.query(FinanceEntry)
        .filter(FinanceEntry.id == entry_id, FinanceEntry.company_id == company_id)
        .first()
    )
    if not entry:
        raise HTTPException(404, "Lançamento financeiro não encontrado.")
    return entry


def _get_open_cash_session(db: Session, company_id: int) -> CashSession | None:
    return (
        db.query(CashSession)
        .filter(CashSession.company_id == company_id, CashSession.status == CashSessionStatus.OPEN)
        .first()
    )


@finance_router.get("/finance/entries", response_model=list[FinanceEntryResponse])
def list_finance_entries(
    user: SessionData = Depends(require_permission("finance.read")),
    db: Session = Depends(get_tenant_db),
    type: FinanceEntryType | None = Query(default=None),
    status: FinanceEntryStatus | None = Query(default=None, description="Filtra pelo status efetivo (inclui OVERDUE calculado)"),
    due_before: date | None = Query(default=None),
    due_after: date | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(FinanceEntry).filter(FinanceEntry.company_id == user.company_id)
    if type is not None:
        query = query.filter(FinanceEntry.type == type)
    if due_before is not None:
        query = query.filter(FinanceEntry.due_date <= due_before)
    if due_after is not None:
        query = query.filter(FinanceEntry.due_date >= due_after)

    rows = query.order_by(FinanceEntry.due_date.asc()).offset(offset).limit(limit).all()
    responses = [_to_response(db, e) for e in rows]
    if status is not None:
        responses = [r for r in responses if r.status == status]
    return responses


@finance_router.post("/finance/entries", response_model=FinanceEntryResponse, status_code=201)
def create_finance_entry(
    payload: FinanceEntryCreate,
    user: SessionData = Depends(require_permission("finance.create")),
    db: Session = Depends(get_tenant_db),
):
    if payload.customer_id is not None:
        customer = (
            db.query(Customer)
            .filter(Customer.id == payload.customer_id, Customer.company_id == user.company_id)
            .first()
        )
        if not customer:
            raise HTTPException(404, "Cliente não encontrado.")

    entry = FinanceEntry(
        company_id=user.company_id,
        branch_id=user.branch_id,
        type=payload.type,
        category=payload.category.strip(),
        description=payload.description.strip(),
        amount=payload.amount,
        due_date=payload.due_date,
        customer_id=payload.customer_id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _to_response(db, entry)


@finance_router.get("/finance/entries/{entry_id}", response_model=FinanceEntryResponse)
def get_finance_entry(
    entry_id: int,
    user: SessionData = Depends(require_permission("finance.read")),
    db: Session = Depends(get_tenant_db),
):
    return _to_response(db, _get_entry_or_404(db, user.company_id, entry_id))


@finance_router.patch("/finance/entries/{entry_id}", response_model=FinanceEntryResponse)
def update_finance_entry(
    entry_id: int,
    payload: FinanceEntryUpdate,
    user: SessionData = Depends(require_permission("finance.create")),
    db: Session = Depends(get_tenant_db),
):
    entry = _get_entry_or_404(db, user.company_id, entry_id)
    if entry.status in (FinanceEntryStatus.PAID, FinanceEntryStatus.CANCELLED):
        raise HTTPException(422, "Lançamento já quitado ou cancelado não pode ser alterado.")

    data = payload.model_dump(exclude_unset=True)
    for field in ("category", "description"):
        if field in data and isinstance(data[field], str):
            data[field] = data[field].strip()
    for key, value in data.items():
        setattr(entry, key, value)

    db.commit()
    db.refresh(entry)
    return _to_response(db, entry)


@finance_router.post("/finance/entries/{entry_id}/cancel", response_model=FinanceEntryResponse)
def cancel_finance_entry(
    entry_id: int,
    user: SessionData = Depends(require_permission("finance.cancel")),
    db: Session = Depends(get_tenant_db),
):
    entry = _get_entry_or_404(db, user.company_id, entry_id)
    if entry.status == FinanceEntryStatus.PAID:
        raise HTTPException(422, "Lançamento já quitado não pode ser cancelado.")
    if entry.status == FinanceEntryStatus.CANCELLED:
        raise HTTPException(422, "Lançamento já está cancelado.")

    entry.status = FinanceEntryStatus.CANCELLED
    db.commit()
    db.refresh(entry)
    log_action(
        db, company_id=user.company_id, user_id=user.user_id, action="finance_entry.cancel",
        entity_type="finance_entry", entity_id=entry.id,
    )
    return _to_response(db, entry)


@finance_router.post("/finance/entries/{entry_id}/pay", response_model=FinanceEntryResponse)
def pay_finance_entry(
    entry_id: int,
    payload: FinanceEntryPayRequest,
    user: SessionData = Depends(require_permission("finance.pay")),
    db: Session = Depends(get_tenant_db),
):
    """Registra pagamento (PAYABLE) ou recebimento (RECEIVABLE). Se houver
    caixa aberto e `register_cash_movement=true` (padrão), lança também um
    CashMovement — saída para PAYABLE, entrada para RECEIVABLE."""
    entry = _get_entry_or_404(db, user.company_id, entry_id)
    if entry.status in (FinanceEntryStatus.PAID, FinanceEntryStatus.CANCELLED):
        raise HTTPException(422, "Lançamento já quitado ou cancelado.")

    remaining = float(entry.amount) - float(entry.paid_amount)
    amount = payload.amount if payload.amount is not None else remaining
    if amount > remaining + 0.01:  # tolerância de arredondamento de centavos
        raise HTTPException(422, f"Valor informado (R$ {amount:.2f}) é maior que o saldo em aberto (R$ {remaining:.2f}).")

    entry.paid_amount = float(entry.paid_amount) + amount
    if entry.paid_amount >= float(entry.amount) - 0.01:
        entry.status = FinanceEntryStatus.PAID
        entry.paid_at = datetime.utcnow()

    if payload.register_cash_movement:
        session = _get_open_cash_session(db, user.company_id)
        if session:
            movement_type = CashMovementType.OUT if entry.type == FinanceEntryType.PAYABLE else CashMovementType.IN
            db.add(
                CashMovement(
                    company_id=user.company_id,
                    cash_session_id=session.id,
                    finance_entry_id=entry.id,
                    type=movement_type,
                    amount=amount,
                    description=f"{'Pagamento' if entry.type == FinanceEntryType.PAYABLE else 'Recebimento'} — {entry.description or entry.category}"[:255],
                    created_by_user_id=user.user_id,
                )
            )

    db.commit()
    db.refresh(entry)
    log_action(
        db, company_id=user.company_id, user_id=user.user_id, action="finance_entry.pay",
        entity_type="finance_entry", entity_id=entry.id, detail=f"Valor: R$ {amount:.2f}",
    )
    return _to_response(db, entry)
