from datetime import datetime
from app.core.clock import utcnow_naive

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_db, require_permission
from app.core.events import publish
from app.core.sessions import SessionData
from app.models.customer import Customer, Vehicle
from app.models.finance import FinanceEntry, FinanceEntryType
from app.models.stock import StockItem, StockMovement, StockMovementType
from app.models.work_order import (
    CLOSED_STATUSES,
    WorkOrder,
    WorkOrderChecklistItem,
    WorkOrderItem,
    WorkOrderStatus,
)
from app.schemas.work_order import (
    ChecklistItemCreate,
    ChecklistItemResponse,
    ChecklistItemUpdate,
    WorkOrderCreate,
    WorkOrderItemAdd,
    WorkOrderItemResponse,
    WorkOrderResponse,
    WorkOrderUpdate,
)
from app.services.audit import log_action

work_order_router = APIRouter()

# Mesmo princípio das demais rotas: company_id nunca vem do corpo da
# requisição — sempre da sessão autenticada, resolvida por get_tenant_db.


def _item_total(item: WorkOrderItem) -> float:
    return float(item.quantity) * float(item.unit_price)


def _total_value(wo: WorkOrder, items: list[WorkOrderItem]) -> float:
    return float(wo.labor_value) + sum(_item_total(i) for i in items) - float(wo.discount_value)


def _to_response(db: Session, wo: WorkOrder) -> WorkOrderResponse:
    customer = db.query(Customer).filter(Customer.id == wo.customer_id).first()
    vehicle = db.query(Vehicle).filter(Vehicle.id == wo.vehicle_id).first() if wo.vehicle_id else None
    items = db.query(WorkOrderItem).filter(WorkOrderItem.work_order_id == wo.id).all()
    checklist_items = (
        db.query(WorkOrderChecklistItem)
        .filter(WorkOrderChecklistItem.work_order_id == wo.id)
        .order_by(WorkOrderChecklistItem.id)
        .all()
    )

    return WorkOrderResponse(
        id=wo.id,
        company_id=wo.company_id,
        branch_id=wo.branch_id,
        customer_id=wo.customer_id,
        vehicle_id=wo.vehicle_id,
        appointment_id=wo.appointment_id,
        mechanic_id=wo.mechanic_id,
        status=wo.status,
        description=wo.description,
        diagnosis=wo.diagnosis,
        labor_value=float(wo.labor_value),
        discount_value=float(wo.discount_value),
        total_value=_total_value(wo, items),
        next_revision_date=wo.next_revision_date,
        created_at=wo.created_at,
        closed_at=wo.closed_at,
        customer_name=customer.name if customer else "",
        vehicle_plate=vehicle.plate if vehicle else "",
        items=[
            WorkOrderItemResponse(
                id=i.id,
                kind=i.kind,
                description=i.description,
                stock_item_id=i.stock_item_id,
                quantity=i.quantity,
                unit_price=float(i.unit_price),
                total_price=_item_total(i),
            )
            for i in items
        ],
        checklist_items=[ChecklistItemResponse.model_validate(c) for c in checklist_items],
    )


def _get_work_order_or_404(db: Session, company_id: int, work_order_id: int) -> WorkOrder:
    wo = (
        db.query(WorkOrder)
        .filter(WorkOrder.id == work_order_id, WorkOrder.company_id == company_id)
        .first()
    )
    if not wo:
        raise HTTPException(404, "Ordem de serviço não encontrada.")
    return wo


def _assert_refs_belong_to_company(
    db: Session, company_id: int, customer_id: int, vehicle_id: int | None
) -> None:
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.company_id == company_id).first()
    if not customer:
        raise HTTPException(404, "Cliente não encontrado.")
    if vehicle_id is not None:
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id, Vehicle.company_id == company_id).first()
        if not vehicle:
            raise HTTPException(404, "Veículo não encontrado.")
        if vehicle.customer_id != customer_id:
            raise HTTPException(422, "Este veículo não pertence ao cliente informado.")


def _add_item(db: Session, company_id: int, work_order_id: int, payload: WorkOrderItemAdd) -> WorkOrderItem:
    if payload.stock_item_id is not None:
        stock_item = (
            db.query(StockItem)
            .filter(StockItem.id == payload.stock_item_id, StockItem.company_id == company_id)
            .first()
        )
        if not stock_item:
            raise HTTPException(404, "Item de estoque informado não encontrado.")

    item = WorkOrderItem(
        company_id=company_id,
        work_order_id=work_order_id,
        stock_item_id=payload.stock_item_id,
        kind=payload.kind,
        description=payload.description.strip(),
        quantity=payload.quantity,
        unit_price=payload.unit_price,
    )
    db.add(item)
    return item


@work_order_router.get("/work-orders", response_model=list[WorkOrderResponse])
def list_work_orders(
    user: SessionData = Depends(require_permission("work_orders.read")),
    db: Session = Depends(get_tenant_db),
    status: WorkOrderStatus | None = Query(default=None),
    customer_id: int | None = Query(default=None),
    mechanic_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(WorkOrder).filter(WorkOrder.company_id == user.company_id)
    if status is not None:
        query = query.filter(WorkOrder.status == status)
    if customer_id is not None:
        query = query.filter(WorkOrder.customer_id == customer_id)
    if mechanic_id is not None:
        query = query.filter(WorkOrder.mechanic_id == mechanic_id)

    rows = query.order_by(WorkOrder.created_at.desc()).offset(offset).limit(limit).all()
    return [_to_response(db, wo) for wo in rows]


@work_order_router.post("/work-orders", response_model=WorkOrderResponse, status_code=201)
def create_work_order(
    payload: WorkOrderCreate,
    user: SessionData = Depends(require_permission("work_orders.create")),
    db: Session = Depends(get_tenant_db),
):
    _assert_refs_belong_to_company(db, user.company_id, payload.customer_id, payload.vehicle_id)

    wo = WorkOrder(
        company_id=user.company_id,
        branch_id=user.branch_id,
        customer_id=payload.customer_id,
        vehicle_id=payload.vehicle_id,
        appointment_id=payload.appointment_id,
        mechanic_id=payload.mechanic_id,
        description=payload.description.strip(),
        diagnosis=payload.diagnosis.strip(),
        labor_value=payload.labor_value,
        discount_value=payload.discount_value,
        next_revision_date=payload.next_revision_date,
    )
    db.add(wo)
    db.flush()

    for item_payload in payload.items:
        _add_item(db, user.company_id, wo.id, item_payload)

    db.commit()
    db.refresh(wo)
    return _to_response(db, wo)


@work_order_router.get("/work-orders/{work_order_id}", response_model=WorkOrderResponse)
def get_work_order(
    work_order_id: int,
    user: SessionData = Depends(require_permission("work_orders.read")),
    db: Session = Depends(get_tenant_db),
):
    wo = _get_work_order_or_404(db, user.company_id, work_order_id)
    return _to_response(db, wo)


@work_order_router.patch("/work-orders/{work_order_id}", response_model=WorkOrderResponse)
def update_work_order(
    work_order_id: int,
    payload: WorkOrderUpdate,
    user: SessionData = Depends(require_permission("work_orders.update")),
    db: Session = Depends(get_tenant_db),
):
    wo = _get_work_order_or_404(db, user.company_id, work_order_id)
    if wo.status in CLOSED_STATUSES:
        raise HTTPException(422, "Ordem de serviço já encerrada (concluída ou cancelada) não pode ser alterada.")

    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] in (WorkOrderStatus.DONE, WorkOrderStatus.CANCELLED):
        raise HTTPException(
            422,
            "Use POST /work-orders/{id}/close para concluir ou "
            "POST /work-orders/{id}/cancel para cancelar (isso baixa estoque e envia comprovante).",
        )

    for field in ("description", "diagnosis"):
        if field in data and isinstance(data[field], str):
            data[field] = data[field].strip()

    for key, value in data.items():
        setattr(wo, key, value)

    db.commit()
    db.refresh(wo)
    return _to_response(db, wo)


@work_order_router.post("/work-orders/{work_order_id}/items", response_model=WorkOrderResponse, status_code=201)
def add_work_order_item(
    work_order_id: int,
    payload: WorkOrderItemAdd,
    user: SessionData = Depends(require_permission("work_orders.update")),
    db: Session = Depends(get_tenant_db),
):
    wo = _get_work_order_or_404(db, user.company_id, work_order_id)
    if wo.status in CLOSED_STATUSES:
        raise HTTPException(422, "Ordem de serviço já encerrada não pode receber novos itens.")

    _add_item(db, user.company_id, wo.id, payload)
    db.commit()
    db.refresh(wo)
    return _to_response(db, wo)


@work_order_router.delete("/work-orders/{work_order_id}/items/{item_id}", response_model=WorkOrderResponse)
def remove_work_order_item(
    work_order_id: int,
    item_id: int,
    user: SessionData = Depends(require_permission("work_orders.update")),
    db: Session = Depends(get_tenant_db),
):
    wo = _get_work_order_or_404(db, user.company_id, work_order_id)
    if wo.status in CLOSED_STATUSES:
        raise HTTPException(422, "Ordem de serviço já encerrada não pode ter itens removidos.")

    item = (
        db.query(WorkOrderItem)
        .filter(WorkOrderItem.id == item_id, WorkOrderItem.work_order_id == work_order_id)
        .first()
    )
    if not item:
        raise HTTPException(404, "Item não encontrado nesta ordem de serviço.")

    db.delete(item)
    db.commit()
    db.refresh(wo)
    return _to_response(db, wo)


@work_order_router.post(
    "/work-orders/{work_order_id}/checklist", response_model=WorkOrderResponse, status_code=201
)
def add_checklist_item(
    work_order_id: int,
    payload: ChecklistItemCreate,
    user: SessionData = Depends(require_permission("work_orders.update")),
    db: Session = Depends(get_tenant_db),
):
    wo = _get_work_order_or_404(db, user.company_id, work_order_id)
    if wo.status in CLOSED_STATUSES:
        raise HTTPException(422, "Ordem de serviço já encerrada não pode receber novos itens de checklist.")

    item = WorkOrderChecklistItem(
        company_id=user.company_id,
        work_order_id=wo.id,
        description=payload.description.strip(),
    )
    db.add(item)
    db.commit()
    db.refresh(wo)
    return _to_response(db, wo)


@work_order_router.patch(
    "/work-orders/{work_order_id}/checklist/{item_id}", response_model=WorkOrderResponse
)
def update_checklist_item(
    work_order_id: int,
    item_id: int,
    payload: ChecklistItemUpdate,
    user: SessionData = Depends(require_permission("work_orders.update")),
    db: Session = Depends(get_tenant_db),
):
    wo = _get_work_order_or_404(db, user.company_id, work_order_id)
    item = (
        db.query(WorkOrderChecklistItem)
        .filter(WorkOrderChecklistItem.id == item_id, WorkOrderChecklistItem.work_order_id == work_order_id)
        .first()
    )
    if not item:
        raise HTTPException(404, "Item de checklist não encontrado nesta ordem de serviço.")

    if payload.status is not None:
        item.status = payload.status
        item.checked_by_user_id = user.user_id
        item.checked_at = utcnow_naive()
    if payload.notes is not None:
        item.notes = payload.notes.strip()

    db.commit()
    db.refresh(wo)
    return _to_response(db, wo)


@work_order_router.delete(
    "/work-orders/{work_order_id}/checklist/{item_id}", response_model=WorkOrderResponse
)
def remove_checklist_item(
    work_order_id: int,
    item_id: int,
    user: SessionData = Depends(require_permission("work_orders.update")),
    db: Session = Depends(get_tenant_db),
):
    wo = _get_work_order_or_404(db, user.company_id, work_order_id)
    if wo.status in CLOSED_STATUSES:
        raise HTTPException(422, "Ordem de serviço já encerrada não pode ter itens de checklist removidos.")

    item = (
        db.query(WorkOrderChecklistItem)
        .filter(WorkOrderChecklistItem.id == item_id, WorkOrderChecklistItem.work_order_id == work_order_id)
        .first()
    )
    if not item:
        raise HTTPException(404, "Item de checklist não encontrado nesta ordem de serviço.")

    db.delete(item)
    db.commit()
    db.refresh(wo)
    return _to_response(db, wo)


@work_order_router.post("/work-orders/{work_order_id}/close", response_model=WorkOrderResponse)
def close_work_order(
    work_order_id: int,
    user: SessionData = Depends(require_permission("work_orders.update")),
    db: Session = Depends(get_tenant_db),
):
    """Conclui a OS: baixa do estoque as peças usadas (um StockMovement OUT
    por item vinculado a um StockItem) e dispara o comprovante por e-mail e
    WhatsApp com valor, material usado e datas do serviço/próxima revisão."""
    wo = _get_work_order_or_404(db, user.company_id, work_order_id)
    if wo.status in CLOSED_STATUSES:
        raise HTTPException(422, "Ordem de serviço já está encerrada.")

    items = db.query(WorkOrderItem).filter(WorkOrderItem.work_order_id == wo.id).all()
    for item in items:
        if item.stock_item_id is None:
            continue
        stock_item = db.query(StockItem).filter(StockItem.id == item.stock_item_id).first()
        if not stock_item:
            continue
        if stock_item.quantity < item.quantity:
            raise HTTPException(
                422,
                f"Estoque insuficiente para '{stock_item.name}': disponível {stock_item.quantity}, "
                f"necessário {item.quantity}.",
            )
        stock_item.quantity -= item.quantity
        db.add(
            StockMovement(
                company_id=user.company_id,
                stock_item_id=stock_item.id,
                work_order_id=wo.id,
                type=StockMovementType.OUT,
                quantity=item.quantity,
                reason=f"Baixa automática pelo fechamento da OS #{wo.id}",
                created_by_user_id=user.user_id,
            )
        )

    wo.status = WorkOrderStatus.DONE
    wo.closed_at = utcnow_naive()
    db.commit()
    db.refresh(wo)

    # "Fechar a OS" não precisa mais saber que isso dispara um comprovante —
    # só publica o evento (ver app/events/handlers.py, FASE 12). Continua
    # síncrono e na mesma sessão de banco, então o comportamento observável
    # é idêntico ao de antes desta fase.
    publish("work_order.closed", db=db, work_order=wo)

    # FASE 6: gera automaticamente a conta a receber do valor total da OS.
    # Vencimento imediato (hoje) — este scaffold não modela prazo de
    # pagamento por cliente/contrato ainda.
    total_value = _total_value(wo, items)
    if total_value > 0:
        db.add(
            FinanceEntry(
                company_id=user.company_id,
                branch_id=wo.branch_id,
                type=FinanceEntryType.RECEIVABLE,
                category="Ordem de Serviço",
                description=f"OS #{wo.id} — {wo.description or 'serviço concluído'}",
                amount=total_value,
                due_date=wo.closed_at.date(),
                customer_id=wo.customer_id,
                work_order_id=wo.id,
            )
        )
        db.commit()

    log_action(
        db, company_id=user.company_id, user_id=user.user_id, action="work_order.close",
        entity_type="work_order", entity_id=wo.id, detail=f"Total: R$ {total_value:.2f}",
    )

    return _to_response(db, wo)


@work_order_router.post("/work-orders/{work_order_id}/cancel", response_model=WorkOrderResponse)
def cancel_work_order(
    work_order_id: int,
    user: SessionData = Depends(require_permission("work_orders.cancel")),
    db: Session = Depends(get_tenant_db),
):
    wo = _get_work_order_or_404(db, user.company_id, work_order_id)
    if wo.status in CLOSED_STATUSES:
        raise HTTPException(422, "Ordem de serviço já está encerrada.")

    wo.status = WorkOrderStatus.CANCELLED
    wo.closed_at = utcnow_naive()
    db.commit()
    db.refresh(wo)
    log_action(
        db, company_id=user.company_id, user_id=user.user_id, action="work_order.cancel",
        entity_type="work_order", entity_id=wo.id,
    )
    return _to_response(db, wo)
