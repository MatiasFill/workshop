from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_db, require_permission
from app.core.sessions import SessionData
from app.models.finance import FinanceEntry, FinanceEntryType
from app.models.purchase import (
    CLOSED_PURCHASE_STATUSES,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderStatus,
    Supplier,
)
from app.models.stock import StockItem, StockMovement, StockMovementType
from app.schemas.purchase import (
    PurchaseOrderCreate,
    PurchaseOrderItemResponse,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
)
from app.services.audit import log_action

purchase_order_router = APIRouter()

# Mesmo princípio das demais rotas: company_id nunca vem do corpo da
# requisição — sempre da sessão autenticada, resolvida por get_tenant_db.


def _item_total(item: PurchaseOrderItem) -> float:
    return float(item.quantity) * float(item.unit_cost)


def _to_response(db: Session, po: PurchaseOrder) -> PurchaseOrderResponse:
    supplier = db.query(Supplier).filter(Supplier.id == po.supplier_id).first()
    items = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.purchase_order_id == po.id).all()

    return PurchaseOrderResponse(
        id=po.id,
        supplier_id=po.supplier_id,
        supplier_name=supplier.name if supplier else "",
        status=po.status,
        notes=po.notes,
        payment_due_date=po.payment_due_date,
        total_value=sum(_item_total(i) for i in items),
        created_at=po.created_at,
        ordered_at=po.ordered_at,
        received_at=po.received_at,
        items=[
            PurchaseOrderItemResponse(
                id=i.id,
                description=i.description,
                stock_item_id=i.stock_item_id,
                quantity=i.quantity,
                unit_cost=float(i.unit_cost),
                total_cost=_item_total(i),
            )
            for i in items
        ],
    )


def _get_purchase_order_or_404(db: Session, company_id: int, po_id: int) -> PurchaseOrder:
    po = (
        db.query(PurchaseOrder)
        .filter(PurchaseOrder.id == po_id, PurchaseOrder.company_id == company_id)
        .first()
    )
    if not po:
        raise HTTPException(404, "Pedido de compra não encontrado.")
    return po


def _add_item(db: Session, company_id: int, po_id: int, payload) -> PurchaseOrderItem:
    if payload.stock_item_id is not None:
        stock_item = (
            db.query(StockItem)
            .filter(StockItem.id == payload.stock_item_id, StockItem.company_id == company_id)
            .first()
        )
        if not stock_item:
            raise HTTPException(404, "Item de estoque informado não encontrado.")

    item = PurchaseOrderItem(
        company_id=company_id,
        purchase_order_id=po_id,
        stock_item_id=payload.stock_item_id,
        description=payload.description.strip(),
        quantity=payload.quantity,
        unit_cost=payload.unit_cost,
    )
    db.add(item)
    return item


@purchase_order_router.get("/purchase-orders", response_model=list[PurchaseOrderResponse])
def list_purchase_orders(
    user: SessionData = Depends(require_permission("purchases.read")),
    db: Session = Depends(get_tenant_db),
    status: PurchaseOrderStatus | None = Query(default=None),
    supplier_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(PurchaseOrder).filter(PurchaseOrder.company_id == user.company_id)
    if status is not None:
        query = query.filter(PurchaseOrder.status == status)
    if supplier_id is not None:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)

    rows = query.order_by(PurchaseOrder.created_at.desc()).offset(offset).limit(limit).all()
    return [_to_response(db, po) for po in rows]


@purchase_order_router.post("/purchase-orders", response_model=PurchaseOrderResponse, status_code=201)
def create_purchase_order(
    payload: PurchaseOrderCreate,
    user: SessionData = Depends(require_permission("purchases.create")),
    db: Session = Depends(get_tenant_db),
):
    supplier = (
        db.query(Supplier)
        .filter(Supplier.id == payload.supplier_id, Supplier.company_id == user.company_id)
        .first()
    )
    if not supplier:
        raise HTTPException(404, "Fornecedor não encontrado.")

    po = PurchaseOrder(
        company_id=user.company_id,
        branch_id=user.branch_id,
        supplier_id=payload.supplier_id,
        notes=payload.notes.strip(),
        payment_due_date=payload.payment_due_date,
        status=PurchaseOrderStatus.ORDERED,
        ordered_at=datetime.utcnow(),
    )
    db.add(po)
    db.flush()

    for item_payload in payload.items:
        _add_item(db, user.company_id, po.id, item_payload)

    db.commit()
    db.refresh(po)
    return _to_response(db, po)


@purchase_order_router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(
    po_id: int,
    user: SessionData = Depends(require_permission("purchases.read")),
    db: Session = Depends(get_tenant_db),
):
    return _to_response(db, _get_purchase_order_or_404(db, user.company_id, po_id))


@purchase_order_router.patch("/purchase-orders/{po_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(
    po_id: int,
    payload: PurchaseOrderUpdate,
    user: SessionData = Depends(require_permission("purchases.update")),
    db: Session = Depends(get_tenant_db),
):
    po = _get_purchase_order_or_404(db, user.company_id, po_id)
    if po.status in CLOSED_PURCHASE_STATUSES:
        raise HTTPException(422, "Pedido de compra já encerrado (recebido ou cancelado) não pode ser alterado.")

    data = payload.model_dump(exclude_unset=True)
    if "notes" in data and isinstance(data["notes"], str):
        data["notes"] = data["notes"].strip()
    for key, value in data.items():
        setattr(po, key, value)

    db.commit()
    db.refresh(po)
    return _to_response(db, po)


@purchase_order_router.post("/purchase-orders/{po_id}/receive", response_model=PurchaseOrderResponse)
def receive_purchase_order(
    po_id: int,
    user: SessionData = Depends(require_permission("purchases.receive")),
    db: Session = Depends(get_tenant_db),
):
    """Recebe a mercadoria: dá entrada no estoque de cada item vinculado a um
    `StockItem` (um `StockMovement` IN por item) e gera automaticamente a
    conta a pagar (`FinanceEntry` PAYABLE) com o valor total do pedido."""
    po = _get_purchase_order_or_404(db, user.company_id, po_id)
    if po.status in CLOSED_PURCHASE_STATUSES:
        raise HTTPException(422, "Pedido de compra já está encerrado.")

    items = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.purchase_order_id == po.id).all()
    if not items:
        raise HTTPException(422, "Pedido de compra sem itens não pode ser recebido.")

    for item in items:
        if item.stock_item_id is None:
            continue
        stock_item = db.query(StockItem).filter(StockItem.id == item.stock_item_id).first()
        if not stock_item:
            continue
        stock_item.quantity += item.quantity
        db.add(
            StockMovement(
                company_id=user.company_id,
                stock_item_id=stock_item.id,
                type=StockMovementType.IN,
                quantity=item.quantity,
                reason=f"Recebimento do pedido de compra #{po.id}",
                created_by_user_id=user.user_id,
            )
        )

    po.status = PurchaseOrderStatus.RECEIVED
    po.received_at = datetime.utcnow()
    db.commit()
    db.refresh(po)

    total_value = sum(_item_total(i) for i in items)
    if total_value > 0:
        supplier = db.query(Supplier).filter(Supplier.id == po.supplier_id).first()
        due = po.payment_due_date or po.received_at.date()
        db.add(
            FinanceEntry(
                company_id=user.company_id,
                branch_id=po.branch_id,
                type=FinanceEntryType.PAYABLE,
                category="Pedido de Compra",
                description=f"PC #{po.id} — {supplier.name if supplier else 'fornecedor'}",
                amount=total_value,
                due_date=due,
            )
        )
        db.commit()

    log_action(
        db, company_id=user.company_id, user_id=user.user_id, action="purchase_order.receive",
        entity_type="purchase_order", entity_id=po.id, detail=f"Total: R$ {total_value:.2f}",
    )

    return _to_response(db, po)


@purchase_order_router.post("/purchase-orders/{po_id}/cancel", response_model=PurchaseOrderResponse)
def cancel_purchase_order(
    po_id: int,
    user: SessionData = Depends(require_permission("purchases.cancel")),
    db: Session = Depends(get_tenant_db),
):
    po = _get_purchase_order_or_404(db, user.company_id, po_id)
    if po.status in CLOSED_PURCHASE_STATUSES:
        raise HTTPException(422, "Pedido de compra já está encerrado.")

    po.status = PurchaseOrderStatus.CANCELLED
    db.commit()
    db.refresh(po)
    log_action(
        db, company_id=user.company_id, user_id=user.user_id, action="purchase_order.cancel",
        entity_type="purchase_order", entity_id=po.id,
    )
    return _to_response(db, po)
