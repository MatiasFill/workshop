"""
Testes da trilha de auditoria (FASE 8).

Requer Redis rodando (ver nota em test_security.py). Não executado neste
ambiente de auditoria — rode localmente com:
    docker compose up -d db redis
    cd backend && pip install -r requirements.txt
    pytest tests/test_audit.py -v
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


def test_audit_logs_require_permission():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "RECEPTION", "recepcaoAUD@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("recepcaoAUD@teste.local", "senha-correta-123")
    assert c.get("/api/audit-logs").status_code == 403  # RECEPTION não tem audit.read


def test_login_is_logged():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteAUD1@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteAUD1@teste.local", "senha-correta-123")
    logs = c.get("/api/audit-logs", params={"action": "auth.login"}).json()
    assert len(logs) >= 1
    assert logs[0]["action"] == "auth.login"


def test_logout_is_logged():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteAUD2@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteAUD2@teste.local", "senha-correta-123")
    assert c.post("/api/auth/logout").status_code == 200

    # a sessão foi revogada, mas o log já foi gravado antes — confirmamos
    # com um segundo login.
    c2 = _login("gerenteAUD2@teste.local", "senha-correta-123")
    logs = c2.get("/api/audit-logs", params={"action": "auth.logout"}).json()
    assert len(logs) >= 1


def test_work_order_close_is_logged():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteAUD3@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteAUD3@teste.local", "senha-correta-123")
    customer_id = c.post("/api/customers", json={"name": "Cliente Auditoria"}).json()["id"]
    wo = c.post("/api/work-orders", json={"customer_id": customer_id, "labor_value": 100}).json()
    c.post(f"/api/work-orders/{wo['id']}/close")

    logs = c.get("/api/audit-logs", params={"action": "work_order.close"}).json()
    assert any(l["entity_id"] == wo["id"] for l in logs)


def test_finance_pay_and_stock_adjust_are_logged():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteAUD4@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteAUD4@teste.local", "senha-correta-123")

    entry = c.post("/api/finance/entries", json={"type": "RECEIVABLE", "amount": 90, "due_date": "2026-10-01"}).json()
    c.post(f"/api/finance/entries/{entry['id']}/pay", json={})
    pay_logs = c.get("/api/audit-logs", params={"action": "finance_entry.pay"}).json()
    assert any(l["entity_id"] == entry["id"] for l in pay_logs)

    stock = c.post("/api/stock", json={"sku": "AUD001", "name": "Item Auditado", "quantity": 5}).json()
    c.post(f"/api/stock/{stock['id']}/adjust", json={"type": "IN", "quantity": 3, "reason": "teste"})
    stock_logs = c.get("/api/audit-logs", params={"action": "stock.adjust"}).json()
    assert any(l["entity_id"] == stock["id"] for l in stock_logs)


def test_purchase_order_receive_is_logged():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "STOCK_MANAGER", "estoqueAUD1@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("estoqueAUD1@teste.local", "senha-correta-123")
    supplier_id = c.post("/api/suppliers", json={"name": "Fornecedor Auditoria"}).json()["id"]
    po = c.post(
        "/api/purchase-orders",
        json={"supplier_id": supplier_id, "items": [{"description": "Peça", "quantity": 1, "unit_cost": 10}]},
    ).json()
    c.post(f"/api/purchase-orders/{po['id']}/receive")

    logs = c.get("/api/audit-logs", params={"action": "purchase_order.receive"}).json()
    assert any(l["entity_id"] == po["id"] for l in logs)


def test_audit_logs_are_isolated_by_company():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteAUD5@teste.local", "senha-correta-123")
        seed_test_tenant(db, "MANAGER", "gerenteAUD6@teste.local", "senha-correta-123")
    finally:
        db.close()

    client_a = _login("gerenteAUD5@teste.local", "senha-correta-123")
    client_b = _login("gerenteAUD6@teste.local", "senha-correta-123")

    logs_a = client_a.get("/api/audit-logs").json()
    logs_b = client_b.get("/api/audit-logs").json()
    ids_a = {l["id"] for l in logs_a}
    ids_b = {l["id"] for l in logs_b}
    assert ids_a.isdisjoint(ids_b)  # nenhuma empresa vê os logs da outra
