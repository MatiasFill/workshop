"""
Testes do módulo de Clientes/Veículos (FASE 2).

Requer Redis rodando (ver nota em test_security.py). Não executado neste
ambiente de auditoria — rode localmente com:
    docker compose up -d db redis
    cd backend && pip install -r requirements.txt
    pytest tests/test_customers.py -v
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
    c = TestClient(app)  # cookie jar isolado por teste
    r = c.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return c


def test_customers_requires_login():
    r = client.get("/api/customers")
    assert r.status_code == 401


def test_receptionist_can_create_customer_with_vehicle():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "RECEPTION", "recepcao1@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("recepcao1@teste.local", "senha-correta-123")
    r = c.post(
        "/api/customers",
        json={
            "name": "Maria Souza",
            "document": "123.456.789-00",
            "phone": "21999990000",
            "vehicles": [{"plate": "abc-1234", "brand": "Fiat", "model": "Uno"}],
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["document"] == "12345678900"  # normalizado, só dígitos
    assert body["vehicles"][0]["plate"] == "ABC1234"  # normalizada, maiúscula sem hífen


def test_mechanic_cannot_create_customer():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MECHANIC", "mecanico3@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("mecanico3@teste.local", "senha-correta-123")
    r = c.post("/api/customers", json={"name": "Cliente Qualquer"})
    assert r.status_code == 403


def test_customers_are_isolated_by_company():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteA@teste.local", "senha-correta-123")
        seed_test_tenant(db, "MANAGER", "gerenteB@teste.local", "senha-correta-123")
    finally:
        db.close()

    client_a = _login("gerenteA@teste.local", "senha-correta-123")
    client_b = _login("gerenteB@teste.local", "senha-correta-123")

    r = client_a.post("/api/customers", json={"name": "Cliente da Empresa A"})
    assert r.status_code == 201
    customer_id = r.json()["id"]

    # Empresa B não pode ver o cliente da empresa A, mesmo sabendo o ID.
    r2 = client_b.get(f"/api/customers/{customer_id}")
    assert r2.status_code == 404

    r3 = client_b.get("/api/customers")
    assert all(item["id"] != customer_id for item in r3.json())


def test_duplicate_document_in_same_company_is_rejected():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteC@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteC@teste.local", "senha-correta-123")
    r1 = c.post("/api/customers", json={"name": "Cliente 1", "document": "111.222.333-44"})
    assert r1.status_code == 201

    r2 = c.post("/api/customers", json={"name": "Cliente 2", "document": "111222333-44"})
    assert r2.status_code == 409


def test_duplicate_plate_in_same_company_is_rejected():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteD@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteD@teste.local", "senha-correta-123")
    r1 = c.post("/api/customers", json={"name": "Cliente 1", "vehicles": [{"plate": "XYZ9999"}]})
    assert r1.status_code == 201
    customer_id = r1.json()["id"]

    r2 = c.post(f"/api/customers/{customer_id}/vehicles", json={"plate": "xyz-9999"})
    assert r2.status_code == 409


def test_delete_customer_is_soft_delete():
    # MANAGER não tem "customers.delete" no catálogo (só ADMIN); usar ADMIN aqui.
    db = SessionLocal()
    try:
        seed_test_tenant(db, "ADMIN", "adminE@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("adminE@teste.local", "senha-correta-123")
    r1 = c.post("/api/customers", json={"name": "Cliente a excluir", "vehicles": [{"plate": "DEL0001"}]})
    customer_id = r1.json()["id"]

    r2 = c.delete(f"/api/customers/{customer_id}")
    assert r2.status_code == 204

    # Ainda existe (soft delete), mas marcado como inativo.
    r3 = c.get(f"/api/customers/{customer_id}")
    assert r3.status_code == 200
    body = r3.json()
    assert body["is_active"] is False
    assert body["vehicles"][0]["is_active"] is False
