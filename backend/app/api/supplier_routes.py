from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_db, require_permission
from app.core.sessions import SessionData
from app.models.purchase import Supplier
from app.schemas.supplier import SupplierCreate, SupplierResponse, SupplierUpdate

supplier_router = APIRouter()

# Mesmo princípio das demais rotas: company_id nunca vem do corpo da
# requisição — sempre da sessão autenticada, resolvida por get_tenant_db.


def _get_supplier_or_404(db: Session, company_id: int, supplier_id: int) -> Supplier:
    supplier = (
        db.query(Supplier)
        .filter(Supplier.id == supplier_id, Supplier.company_id == company_id)
        .first()
    )
    if not supplier:
        raise HTTPException(404, "Fornecedor não encontrado.")
    return supplier


@supplier_router.get("/suppliers", response_model=list[SupplierResponse])
def list_suppliers(
    user: SessionData = Depends(require_permission("suppliers.read")),
    db: Session = Depends(get_tenant_db),
    q: str | None = Query(default=None, max_length=255),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(Supplier).filter(Supplier.company_id == user.company_id)
    if is_active is not None:
        query = query.filter(Supplier.is_active == is_active)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(Supplier.name.ilike(like), Supplier.document.ilike(like)))

    return query.order_by(Supplier.name.asc()).offset(offset).limit(limit).all()


@supplier_router.post("/suppliers", response_model=SupplierResponse, status_code=201)
def create_supplier(
    payload: SupplierCreate,
    user: SessionData = Depends(require_permission("suppliers.create")),
    db: Session = Depends(get_tenant_db),
):
    supplier = Supplier(
        company_id=user.company_id,
        name=payload.name.strip(),
        document=payload.document.strip(),
        phone=payload.phone.strip(),
        email=payload.email.strip(),
        notes=payload.notes.strip(),
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@supplier_router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: int,
    user: SessionData = Depends(require_permission("suppliers.read")),
    db: Session = Depends(get_tenant_db),
):
    return _get_supplier_or_404(db, user.company_id, supplier_id)


@supplier_router.patch("/suppliers/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    user: SessionData = Depends(require_permission("suppliers.create")),
    db: Session = Depends(get_tenant_db),
):
    supplier = _get_supplier_or_404(db, user.company_id, supplier_id)
    data = payload.model_dump(exclude_unset=True)
    for field in ("name", "document", "phone", "email", "notes"):
        if field in data and isinstance(data[field], str):
            data[field] = data[field].strip()
    for key, value in data.items():
        setattr(supplier, key, value)

    db.commit()
    db.refresh(supplier)
    return supplier
