from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_db, require_permission
from app.core.sessions import SessionData
from app.models.customer import Customer, Vehicle
from app.schemas.customer import (
    CustomerCreate,
    CustomerListItem,
    CustomerResponse,
    CustomerUpdate,
    VehicleCreate,
    VehicleResponse,
    VehicleUpdate,
)

customer_router = APIRouter()

# Assim como em routes.py (FASE 1), company_id nunca vem do corpo da
# requisição — sempre da sessão autenticada (user.company_id), resolvida por
# get_tenant_db/require_permission. Isso vale tanto para o filtro em código
# quanto para o SET LOCAL que alimenta a RLS no Postgres.


def _get_customer_or_404(db: Session, company_id: int, customer_id: int) -> Customer:
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.company_id == company_id)
        .first()
    )
    if not customer:
        raise HTTPException(404, "Cliente não encontrado.")
    return customer


def _get_vehicle_or_404(db: Session, company_id: int, customer_id: int, vehicle_id: int) -> Vehicle:
    vehicle = (
        db.query(Vehicle)
        .filter(
            Vehicle.id == vehicle_id,
            Vehicle.customer_id == customer_id,
            Vehicle.company_id == company_id,
        )
        .first()
    )
    if not vehicle:
        raise HTTPException(404, "Veículo não encontrado.")
    return vehicle


def _assert_unique_document(db: Session, company_id: int, document: str, exclude_id: int | None = None) -> None:
    if not document:
        return
    query = db.query(Customer).filter(Customer.company_id == company_id, Customer.document == document)
    if exclude_id is not None:
        query = query.filter(Customer.id != exclude_id)
    if query.first():
        raise HTTPException(409, "Já existe um cliente com esse CPF/CNPJ nesta empresa.")


def _assert_unique_plate(db: Session, company_id: int, plate: str, exclude_id: int | None = None) -> None:
    query = db.query(Vehicle).filter(Vehicle.company_id == company_id, Vehicle.plate == plate)
    if exclude_id is not None:
        query = query.filter(Vehicle.id != exclude_id)
    if query.first():
        raise HTTPException(409, "Já existe um veículo com essa placa nesta empresa.")


# ---------------------------------------------------------------- Clientes


@customer_router.get("/customers", response_model=list[CustomerListItem])
def list_customers(
    user: SessionData = Depends(require_permission("customers.read")),
    db: Session = Depends(get_tenant_db),
    q: str | None = Query(default=None, max_length=255, description="Busca por nome, documento, telefone ou e-mail"),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    vehicle_count = func.count(Vehicle.id)
    query = (
        db.query(Customer, vehicle_count)
        .outerjoin(Vehicle, Vehicle.customer_id == Customer.id)
        .filter(Customer.company_id == user.company_id)
        .group_by(Customer.id)
    )
    if is_active is not None:
        query = query.filter(Customer.is_active == is_active)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Customer.name.ilike(like),
                Customer.document.ilike(like),
                Customer.phone.ilike(like),
                Customer.email.ilike(like),
            )
        )

    rows = query.order_by(Customer.name.asc()).offset(offset).limit(limit).all()
    return [
        CustomerListItem(
            id=c.id,
            name=c.name,
            document=c.document,
            phone=c.phone,
            email=c.email,
            is_active=c.is_active,
            is_anonymized=c.is_anonymized,
            vehicle_count=count,
            created_at=c.created_at,
        )
        for c, count in rows
    ]


@customer_router.post("/customers", response_model=CustomerResponse, status_code=201)
def create_customer(
    payload: CustomerCreate,
    user: SessionData = Depends(require_permission("customers.create")),
    db: Session = Depends(get_tenant_db),
):
    _assert_unique_document(db, user.company_id, payload.document)

    plates_seen: set[str] = set()
    for v in payload.vehicles:
        if v.plate in plates_seen:
            raise HTTPException(422, f"Placa duplicada no mesmo cadastro: {v.plate}.")
        plates_seen.add(v.plate)
        _assert_unique_plate(db, user.company_id, v.plate)

    customer = Customer(
        company_id=user.company_id,
        name=payload.name.strip(),
        document=payload.document,
        phone=payload.phone.strip(),
        email=payload.email.strip(),
        address=payload.address.strip(),
        notes=payload.notes.strip(),
    )
    db.add(customer)
    db.flush()

    for v in payload.vehicles:
        db.add(
            Vehicle(
                company_id=user.company_id,
                customer_id=customer.id,
                plate=v.plate,
                brand=v.brand.strip(),
                model=v.model.strip(),
                year=v.year,
                color=v.color.strip(),
                km=v.km,
                notes=v.notes.strip(),
            )
        )

    db.commit()
    db.refresh(customer)
    return customer


@customer_router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    user: SessionData = Depends(require_permission("customers.read")),
    db: Session = Depends(get_tenant_db),
):
    return _get_customer_or_404(db, user.company_id, customer_id)


@customer_router.patch("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    user: SessionData = Depends(require_permission("customers.update")),
    db: Session = Depends(get_tenant_db),
):
    customer = _get_customer_or_404(db, user.company_id, customer_id)
    data = payload.model_dump(exclude_unset=True)

    if "document" in data and data["document"]:
        _assert_unique_document(db, user.company_id, data["document"], exclude_id=customer.id)

    for field in ("name", "document", "phone", "email", "address", "notes"):
        if field in data and isinstance(data[field], str):
            data[field] = data[field].strip()

    for key, value in data.items():
        setattr(customer, key, value)

    db.commit()
    db.refresh(customer)
    return customer


@customer_router.delete("/customers/{customer_id}", status_code=204)
def delete_customer(
    customer_id: int,
    user: SessionData = Depends(require_permission("customers.delete")),
    db: Session = Depends(get_tenant_db),
):
    """Exclusão lógica (is_active=False), para preservar histórico de OS
    futuras que referenciem este cliente/veículos — nunca deleta a linha."""
    customer = _get_customer_or_404(db, user.company_id, customer_id)
    customer.is_active = False
    for vehicle in customer.vehicles:
        vehicle.is_active = False
    db.commit()
    return None


# ----------------------------------------------------------------- Veículos


@customer_router.post("/customers/{customer_id}/vehicles", response_model=VehicleResponse, status_code=201)
def add_vehicle(
    customer_id: int,
    payload: VehicleCreate,
    user: SessionData = Depends(require_permission("customers.update")),
    db: Session = Depends(get_tenant_db),
):
    customer = _get_customer_or_404(db, user.company_id, customer_id)
    _assert_unique_plate(db, user.company_id, payload.plate)

    vehicle = Vehicle(
        company_id=user.company_id,
        customer_id=customer.id,
        plate=payload.plate,
        brand=payload.brand.strip(),
        model=payload.model.strip(),
        year=payload.year,
        color=payload.color.strip(),
        km=payload.km,
        notes=payload.notes.strip(),
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@customer_router.patch("/customers/{customer_id}/vehicles/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    customer_id: int,
    vehicle_id: int,
    payload: VehicleUpdate,
    user: SessionData = Depends(require_permission("customers.update")),
    db: Session = Depends(get_tenant_db),
):
    vehicle = _get_vehicle_or_404(db, user.company_id, customer_id, vehicle_id)
    data = payload.model_dump(exclude_unset=True)

    if "plate" in data and data["plate"]:
        _assert_unique_plate(db, user.company_id, data["plate"], exclude_id=vehicle.id)

    for field in ("brand", "model", "color", "notes"):
        if field in data and isinstance(data[field], str):
            data[field] = data[field].strip()

    for key, value in data.items():
        setattr(vehicle, key, value)

    db.commit()
    db.refresh(vehicle)
    return vehicle


@customer_router.delete("/customers/{customer_id}/vehicles/{vehicle_id}", status_code=204)
def delete_vehicle(
    customer_id: int,
    vehicle_id: int,
    user: SessionData = Depends(require_permission("customers.delete")),
    db: Session = Depends(get_tenant_db),
):
    vehicle = _get_vehicle_or_404(db, user.company_id, customer_id, vehicle_id)
    vehicle.is_active = False  # exclusão lógica, mesmo motivo do cliente
    db.commit()
    return None
