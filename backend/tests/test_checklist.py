"""
Testes do checklist de inspeção veicular na OS (FASE 13).

Mesma observação do test_work_orders.py: requer Redis, não executado neste
ambiente de auditoria — rode localmente com:
    docker compose up -d db redis
    cd backend && pip install -r requirements.txt
    pytest tests/test_checklist.py -v
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


def _create_open_work_order(c: TestClient, customer_name: str) -> int:
    customer_id = _create_customer(c, customer_name)
    r = c.post("/api/work-orders", json={"customer_id": customer_id, "labor_value": 100})
    assert r.status_code == 201
    return r.json()["id"]


def test_add_and_list_checklist_item():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteCL1@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteCL1@teste.local", "senha-correta-123")
    wo_id = _create_open_work_order(c, "Cliente Checklist 1")

    r = c.post(f"/api/work-orders/{wo_id}/checklist", json={"description": "Freios"})
    assert r.status_code == 201
    wo = r.json()
    assert len(wo["checklist_items"]) == 1
    item = wo["checklist_items"][0]
    assert item["description"] == "Freios"
    assert item["status"] == "NOT_CHECKED"
    assert item["checked_by_user_id"] is None


def test_update_checklist_item_status_and_notes():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteCL2@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteCL2@teste.local", "senha-correta-123")
    wo_id = _create_open_work_order(c, "Cliente Checklist 2")

    r = c.post(f"/api/work-orders/{wo_id}/checklist", json={"description": "Pneus"})
    item_id = r.json()["checklist_items"][0]["id"]

    r2 = c.patch(
        f"/api/work-orders/{wo_id}/checklist/{item_id}",
        json={"status": "ATTENTION", "notes": "Desgaste irregular no dianteiro direito"},
    )
    assert r2.status_code == 200
    item = r2.json()["checklist_items"][0]
    assert item["status"] == "ATTENTION"
    assert item["notes"] == "Desgaste irregular no dianteiro direito"
    assert item["checked_by_user_id"] is not None
    assert item["checked_at"] is not None


def test_remove_checklist_item():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteCL3@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteCL3@teste.local", "senha-correta-123")
    wo_id = _create_open_work_order(c, "Cliente Checklist 3")

    r = c.post(f"/api/work-orders/{wo_id}/checklist", json={"description": "Óleo"})
    item_id = r.json()["checklist_items"][0]["id"]

    r2 = c.delete(f"/api/work-orders/{wo_id}/checklist/{item_id}")
    assert r2.status_code == 200
    assert r2.json()["checklist_items"] == []


def test_checklist_item_not_found_returns_404():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteCL4@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteCL4@teste.local", "senha-correta-123")
    wo_id = _create_open_work_order(c, "Cliente Checklist 4")

    r = c.patch(f"/api/work-orders/{wo_id}/checklist/999999", json={"status": "OK"})
    assert r.status_code == 404


def test_cannot_add_checklist_item_to_closed_work_order():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteCL5@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteCL5@teste.local", "senha-correta-123")
    wo_id = _create_open_work_order(c, "Cliente Checklist 5")
    assert c.post(f"/api/work-orders/{wo_id}/close").status_code == 200

    r = c.post(f"/api/work-orders/{wo_id}/checklist", json={"description": "Suspensão"})
    assert r.status_code == 422


def test_reception_cannot_manage_checklist():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "RECEPTION", "recepcaoCL@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("recepcaoCL@teste.local", "senha-correta-123")
    wo_id = _create_open_work_order(c, "Cliente Checklist 6")

    r = c.post(f"/api/work-orders/{wo_id}/checklist", json={"description": "Bateria"})
    assert r.status_code == 403  # RECEPTION tem work_orders.create mas não .update


def test_checklist_is_isolated_by_company():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteCL7@teste.local", "senha-correta-123")
        seed_test_tenant(db, "MANAGER", "gerenteCL8@teste.local", "senha-correta-123")
    finally:
        db.close()

    client_a = _login("gerenteCL7@teste.local", "senha-correta-123")
    client_b = _login("gerenteCL8@teste.local", "senha-correta-123")

    wo_id = _create_open_work_order(client_a, "Cliente Empresa A Checklist")
    r = client_a.post(f"/api/work-orders/{wo_id}/checklist", json={"description": "Filtro de ar"})
    item_id = r.json()["checklist_items"][0]["id"]

    r2 = client_b.patch(f"/api/work-orders/{wo_id}/checklist/{item_id}", json={"status": "OK"})
    assert r2.status_code == 404  # OS de outra empresa não é visível (RLS)
