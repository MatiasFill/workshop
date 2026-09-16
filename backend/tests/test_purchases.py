"""
Testes de Fornecedores e Pedidos de Compra (FASE 7).

Requer Redis rodando (ver nota em test_security.py). Não executado neste
ambiente de auditoria — rode localmente com:
    docker compose up -d db redis
    cd backend && pip install -r requirements.txt
    pytest tests/test_purchases.py -v
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_security.db")
os.environ.setdefault("SESSION_COOKIE_SECURE", "false")

from fastapi.testclient import TestClient

from app.db.session import Base, SessionLocal, engine
from app.main import app
from tests.conftest import seed_test_tenant

client = TestClient(app)


def setup_module():
    Base.metadata.create_all(bind=engine)


def _login(email: str, password: str) -> TestClient:
    c = TestClient(app)
    r = c.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return c


def _create_supplier(c: TestClient, name: str) -> int:
    r = c.post("/api/suppliers", json={"name": name})
    assert r.status_code == 201
    return r.json()["id"]


def _create_stock_item(c: TestClient, sku: str, quantity: int = 0) -> int:
    r = c.post("/api/stock", json={"sku": sku, "name": f"Peça {sku}", "quantity": quantity, "min_quantity": 2})
    assert r.status_code == 201
    return r.json()["id"]


def test_purchase_orders_require_login():
    r = client.get("/api/purchase-orders")
    assert r.status_code == 401


def test_receive_purchase_order_adds_stock_and_creates_payable():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "STOCK_MANAGER", "compras1@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("compras1@teste.local", "senha-correta-123")
    supplier_id = _create_supplier(c, "Fornecedor Peças LTDA")
    stock_id = _create_stock_item(c, "COR001", quantity=2)

    r = c.post(
        "/api/purchase-orders",
        json={
            "supplier_id": supplier_id,
            "payment_due_date": "2026-10-10",
            "items": [{"description": "Correia dentada", "stock_item_id": stock_id, "quantity": 10, "unit_cost": 15}],
        },
    )
    assert r.status_code == 201
    po = r.json()
    assert po["status"] == "ORDERED"
    assert po["total_value"] == 150

    r2 = c.post(f"/api/purchase-orders/{po['id']}/receive")
    assert r2.status_code == 200
    assert r2.json()["status"] == "RECEIVED"

    stock_after = c.get(f"/api/stock/{stock_id}").json()
    assert stock_after["quantity"] == 12  # 2 + 10 recebidas

    payables = c.get("/api/finance/entries", params={"type": "PAYABLE"}).json()
    relevant = [p for p in payables if p["description"].startswith(f"PC #{po['id']}")]
    assert len(relevant) == 1
    assert relevant[0]["amount"] == 150
    assert relevant[0]["due_date"] == "2026-10-10"


def test_cannot_receive_purchase_order_twice():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "STOCK_MANAGER", "compras2@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("compras2@teste.local", "senha-correta-123")
    supplier_id = _create_supplier(c, "Fornecedor 2")

    r = c.post("/api/purchase-orders", json={"supplier_id": supplier_id, "items": [{"description": "Óleo", "quantity": 1, "unit_cost": 40}]})
    po_id = r.json()["id"]

    assert c.post(f"/api/purchase-orders/{po_id}/receive").status_code == 200
    assert c.post(f"/api/purchase-orders/{po_id}/receive").status_code == 422


def test_cannot_receive_purchase_order_without_items():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "STOCK_MANAGER", "compras3@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("compras3@teste.local", "senha-correta-123")
    supplier_id = _create_supplier(c, "Fornecedor 3")

    r = c.post("/api/purchase-orders", json={"supplier_id": supplier_id})
    po_id = r.json()["id"]

    r2 = c.post(f"/api/purchase-orders/{po_id}/receive")
    assert r2.status_code == 422


def test_reception_cannot_access_purchases():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "RECEPTION", "recepcaoPC@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("recepcaoPC@teste.local", "senha-correta-123")
    assert c.get("/api/purchase-orders").status_code == 403
    assert c.get("/api/suppliers").status_code == 403


def test_purchase_orders_are_isolated_by_company():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "STOCK_MANAGER", "compras4@teste.local", "senha-correta-123")
        seed_test_tenant(db, "STOCK_MANAGER", "compras5@teste.local", "senha-correta-123")
    finally:
        db.close()

    client_a = _login("compras4@teste.local", "senha-correta-123")
    client_b = _login("compras5@teste.local", "senha-correta-123")

    supplier_id = _create_supplier(client_a, "Fornecedor Empresa A")
    r = client_a.post("/api/purchase-orders", json={"supplier_id": supplier_id})
    po_id = r.json()["id"]

    assert client_b.get(f"/api/purchase-orders/{po_id}").status_code == 404
