"""
Testes de Ordens de Serviço, Estoque e Notificações (FASE 4/5).

Requer Redis rodando (ver nota em test_security.py). Não executado neste
ambiente de auditoria — rode localmente com:
    docker compose up -d db redis
    cd backend && pip install -r requirements.txt
    pytest tests/test_work_orders.py -v

Sem SMTP/WhatsApp configurados no ambiente de teste, os envios de
notificação ficam como SKIPPED (comportamento esperado e verificado abaixo,
não uma falha) — ver app/services/notifications.py.
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


def _create_customer(c: TestClient, name: str) -> int:
    r = c.post("/api/customers", json={"name": name})
    assert r.status_code == 201
    return r.json()["id"]


def _create_stock_item(c: TestClient, sku: str, quantity: int = 10) -> int:
    r = c.post(
        "/api/stock",
        json={"sku": sku, "name": f"Peça {sku}", "quantity": quantity, "min_quantity": 2, "cost_price": 10, "sale_price": 25},
    )
    assert r.status_code == 201
    return r.json()["id"]


def test_work_orders_requires_login():
    r = client.get("/api/work-orders")
    assert r.status_code == 401


def test_close_work_order_deducts_stock_and_logs_notifications():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteWO1@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteWO1@teste.local", "senha-correta-123")
    customer_id = _create_customer(c, "Cliente OS 1")
    stock_id = _create_stock_item(c, "FLT001", quantity=10)

    r = c.post(
        "/api/work-orders",
        json={
            "customer_id": customer_id,
            "labor_value": 150,
            "next_revision_date": "2027-01-15",
            "items": [
                {"kind": "PART", "description": "Filtro de óleo", "stock_item_id": stock_id, "quantity": 2, "unit_price": 40},
                {"kind": "SERVICE", "description": "Troca de óleo", "quantity": 1, "unit_price": 0},
            ],
        },
    )
    assert r.status_code == 201
    wo = r.json()
    assert wo["status"] == "OPEN"
    assert wo["total_value"] == 150 + 2 * 40  # labor + parts, sem serviço extra e sem desconto

    r2 = c.post(f"/api/work-orders/{wo['id']}/close")
    assert r2.status_code == 200
    assert r2.json()["status"] == "DONE"

    stock_after = c.get(f"/api/stock/{stock_id}").json()
    assert stock_after["quantity"] == 8  # 10 - 2 usadas na OS

    notifications = c.get("/api/notifications").json()
    relevant = [n for n in notifications if n["work_order_id"] == wo["id"]]
    assert len(relevant) == 2  # email + whatsapp
    assert all(n["status"] == "SKIPPED" for n in relevant)  # sem SMTP/WhatsApp configurado no teste


def test_cannot_close_work_order_with_insufficient_stock():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteWO2@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteWO2@teste.local", "senha-correta-123")
    customer_id = _create_customer(c, "Cliente OS 2")
    stock_id = _create_stock_item(c, "FLT002", quantity=1)

    r = c.post(
        "/api/work-orders",
        json={
            "customer_id": customer_id,
            "items": [{"kind": "PART", "description": "Pastilha de freio", "stock_item_id": stock_id, "quantity": 5, "unit_price": 30}],
        },
    )
    wo_id = r.json()["id"]

    r2 = c.post(f"/api/work-orders/{wo_id}/close")
    assert r2.status_code == 422

    stock_after = c.get(f"/api/stock/{stock_id}").json()
    assert stock_after["quantity"] == 1  # nada foi baixado, a OS não fechou


def test_cannot_close_work_order_twice():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteWO3@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteWO3@teste.local", "senha-correta-123")
    customer_id = _create_customer(c, "Cliente OS 3")

    r = c.post("/api/work-orders", json={"customer_id": customer_id, "labor_value": 80})
    wo_id = r.json()["id"]

    assert c.post(f"/api/work-orders/{wo_id}/close").status_code == 200
    assert c.post(f"/api/work-orders/{wo_id}/close").status_code == 422


def test_reception_cannot_close_work_order():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "RECEPTION", "recepcaoWO@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("recepcaoWO@teste.local", "senha-correta-123")
    customer_id = _create_customer(c, "Cliente OS 4")
    r = c.post("/api/work-orders", json={"customer_id": customer_id})
    assert r.status_code == 201

    r2 = c.post(f"/api/work-orders/{r.json()['id']}/close")
    assert r2.status_code == 403  # RECEPTION tem work_orders.create mas não .update


def test_work_orders_are_isolated_by_company():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteWO5@teste.local", "senha-correta-123")
        seed_test_tenant(db, "MANAGER", "gerenteWO6@teste.local", "senha-correta-123")
    finally:
        db.close()

    client_a = _login("gerenteWO5@teste.local", "senha-correta-123")
    client_b = _login("gerenteWO6@teste.local", "senha-correta-123")

    customer_id = _create_customer(client_a, "Cliente Empresa A")
    r = client_a.post("/api/work-orders", json={"customer_id": customer_id})
    wo_id = r.json()["id"]

    r2 = client_b.get(f"/api/work-orders/{wo_id}")
    assert r2.status_code == 404


def test_stock_adjust_rejects_negative_result():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "STOCK_MANAGER", "estoqueWO1@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("estoqueWO1@teste.local", "senha-correta-123")
    stock_id = _create_stock_item(c, "OLE001", quantity=3)

    r = c.post(f"/api/stock/{stock_id}/adjust", json={"type": "OUT", "quantity": 10, "reason": "teste"})
    assert r.status_code == 422

    r2 = c.post(f"/api/stock/{stock_id}/adjust", json={"type": "IN", "quantity": 5, "reason": "reposição"})
    assert r2.status_code == 200
    assert r2.json()["quantity"] == 8


def test_reports_dashboard_requires_permission():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MECHANIC", "mecanicoWO1@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("mecanicoWO1@teste.local", "senha-correta-123")
    r = c.get("/api/reports/dashboard")
    assert r.status_code == 403  # MECHANIC não tem reports.read


def test_reports_dashboard_reflects_closed_work_order():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteWO7@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteWO7@teste.local", "senha-correta-123")
    customer_id = _create_customer(c, "Cliente Dashboard")
    r = c.post("/api/work-orders", json={"customer_id": customer_id, "labor_value": 200})
    c.post(f"/api/work-orders/{r.json()['id']}/close")

    dashboard = c.get("/api/reports/dashboard").json()
    assert dashboard["customers_total"] >= 1
    assert dashboard["revenue_this_month"] >= 200
