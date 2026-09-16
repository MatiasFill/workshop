from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_db, require_permission
from app.core.sessions import SessionData
from app.models.stock import StockItem, StockMovement, StockMovementType
from app.schemas.stock import (
    StockAdjustRequest,
    StockItemCreate,
    StockItemResponse,
    StockItemUpdate,
    StockMovementResponse,
)
from app.services.audit import log_action

stock_router = APIRouter()

# Mesmo princípio das demais rotas: company_id nunca vem do corpo da
# requisição — sempre da sessão autenticada, resolvida por get_tenant_db.


def _to_response(item: StockItem) -> StockItemResponse:
    return StockItemResponse(
        id=item.id,
        sku=item.sku,
        name=item.name,
        unit=item.unit,
        quantity=item.quantity,
        min_quantity=item.min_quantity,
        cost_price=float(item.cost_price),
        sale_price=float(item.sale_price),
        notes=item.notes,
        is_active=item.is_active,
        is_low_stock=item.quantity <= item.min_quantity,
        created_at=item.created_at,
    )


def _get_item_or_404(db: Session, company_id: int, item_id: int) -> StockItem:
    item = db.query(StockItem).filter(StockItem.id == item_id, StockItem.company_id == company_id).first()
    if not item:
        raise HTTPException(404, "Item de estoque não encontrado.")
    return item


def _assert_unique_sku(db: Session, company_id: int, sku: str, exclude_id: int | None = None) -> None:
    query = db.query(StockItem).filter(StockItem.company_id == company_id, StockItem.sku == sku)
    if exclude_id is not None:
        query = query.filter(StockItem.id != exclude_id)
    if query.first():
        raise HTTPException(409, "Já existe um item de estoque com esse SKU nesta empresa.")


@stock_router.get("/stock", response_model=list[StockItemResponse])
def list_stock_items(
    user: SessionData = Depends(require_permission("stock.read")),
    db: Session = Depends(get_tenant_db),
    q: str | None = Query(default=None, max_length=255, description="Busca por SKU ou nome"),
    only_low_stock: bool = Query(default=False),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(StockItem).filter(StockItem.company_id == user.company_id)
    if is_active is not None:
        query = query.filter(StockItem.is_active == is_active)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(StockItem.sku.ilike(like), StockItem.name.ilike(like)))
    if only_low_stock:
        query = query.filter(StockItem.quantity <= StockItem.min_quantity)

    rows = query.order_by(StockItem.name.asc()).offset(offset).limit(limit).all()
    return [_to_response(item) for item in rows]


@stock_router.post("/stock", response_model=StockItemResponse, status_code=201)
def create_stock_item(
    payload: StockItemCreate,
    user: SessionData = Depends(require_permission("stock.create")),
    db: Session = Depends(get_tenant_db),
):
    _assert_unique_sku(db, user.company_id, payload.sku)

    item = StockItem(
        company_id=user.company_id,
        sku=payload.sku,
        name=payload.name.strip(),
        unit=payload.unit.strip() or "un",
        quantity=payload.quantity,
        min_quantity=payload.min_quantity,
        cost_price=payload.cost_price,
        sale_price=payload.sale_price,
        notes=payload.notes.strip(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_response(item)


@stock_router.get("/stock/{item_id}", response_model=StockItemResponse)
def get_stock_item(
    item_id: int,
    user: SessionData = Depends(require_permission("stock.read")),
    db: Session = Depends(get_tenant_db),
):
    return _to_response(_get_item_or_404(db, user.company_id, item_id))


@stock_router.patch("/stock/{item_id}", response_model=StockItemResponse)
def update_stock_item(
    item_id: int,
    payload: StockItemUpdate,
    user: SessionData = Depends(require_permission("stock.create")),
    db: Session = Depends(get_tenant_db),
):
    item = _get_item_or_404(db, user.company_id, item_id)
    data = payload.model_dump(exclude_unset=True)

    for field in ("name", "unit", "notes"):
        if field in data and isinstance(data[field], str):
            data[field] = data[field].strip()

    for key, value in data.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return _to_response(item)


@stock_router.post("/stock/{item_id}/adjust", response_model=StockItemResponse)
def adjust_stock_item(
    item_id: int,
    payload: StockAdjustRequest,
    user: SessionData = Depends(require_permission("stock.adjust")),
    db: Session = Depends(get_tenant_db),
):
    """Ajuste manual (entrada, saída ou correção de contagem). Toda mudança
    de quantidade — inclusive a baixa automática por fechamento de OS — passa
    por um StockMovement, nunca altera `quantity` "solto"."""
    item = _get_item_or_404(db, user.company_id, item_id)

    if payload.type == StockMovementType.OUT and payload.quantity > item.quantity:
        raise HTTPException(422, "Quantidade de saída maior que o estoque disponível.")

    if payload.type == StockMovementType.OUT:
        item.quantity -= payload.quantity
    else:
        # IN e ADJUSTMENT (correção de contagem para mais) aumentam o saldo.
        # Uma correção para baixo deve ser lançada como OUT com o motivo
        # explicado — mantém o sinal de `quantity` sempre positivo no log.
        item.quantity += payload.quantity

    db.add(
        StockMovement(
            company_id=user.company_id,
            stock_item_id=item.id,
            type=payload.type,
            quantity=payload.quantity,
            reason=payload.reason.strip(),
            created_by_user_id=user.user_id,
        )
    )
    db.commit()
    db.refresh(item)
    log_action(
        db, company_id=user.company_id, user_id=user.user_id, action="stock.adjust",
        entity_type="stock_item", entity_id=item.id,
        detail=f"{payload.type.value} {payload.quantity} — {payload.reason.strip() or 'sem motivo informado'}",
    )
    return _to_response(item)


@stock_router.get("/stock/{item_id}/movements", response_model=list[StockMovementResponse])
def list_stock_movements(
    item_id: int,
    user: SessionData = Depends(require_permission("stock.read")),
    db: Session = Depends(get_tenant_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    _get_item_or_404(db, user.company_id, item_id)
    rows = (
        db.query(StockMovement)
        .filter(StockMovement.stock_item_id == item_id, StockMovement.company_id == user.company_id)
        .order_by(StockMovement.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return rows
