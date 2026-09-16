"""
Testes de LGPD — exportação de dados e anonimização de cliente (FASE 9).

Requer Redis rodando (ver nota em test_security.py). Não executado neste
ambiente de auditoria — rode localmente com:
    docker compose up -d db redis
    cd backend && pip install -r requirements.txt
    pytest tests/test_lgpd.py -v
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


def test_lgpd_routes_require_permission():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "RECEPTION", "recepcaoLGPD@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("recepcaoLGPD@teste.local", "senha-correta-123")
    customer_id = c.post("/api/customers", json={"name": "Cliente X"}).json()["id"]

    assert c.get(f"/api/customers/{customer_id}/export-data").status_code == 403
    assert c.post(f"/api/customers/{customer_id}/anonymize").status_code == 403


def test_export_customer_data_includes_related_records():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteLGPD1@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteLGPD1@teste.local", "senha-correta-123")
    customer = c.post(
        "/api/customers",
        json={"name": "Maria Exportação", "email": "maria@example.com", "phone": "11999990000"},
    ).json()
    wo = c.post("/api/work-orders", json={"customer_id": customer["id"], "labor_value": 200}).json()
    c.post(f"/api/work-orders/{wo['id']}/close")

    export = c.get(f"/api/customers/{customer['id']}/export-data").json()
    assert export["customer"]["name"] == "Maria Exportação"
    assert export["customer"]["email"] == "maria@example.com"
    assert any(w["id"] == wo["id"] for w in export["work_orders"])
    assert len(export["finance_entries"]) >= 1  # a OS concluída gerou uma RECEIVABLE
    assert len(export["notifications"]) >= 2  # comprovante por e-mail + WhatsApp (SKIPPED sem SMTP)


def test_anonymize_customer_scrubs_pii_but_keeps_business_records():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteLGPD2@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteLGPD2@teste.local", "senha-correta-123")
    customer = c.post(
        "/api/customers",
        json={"name": "João Esquecimento", "email": "joao@example.com", "phone": "11988887777", "document": "12345678900"},
    ).json()
    wo = c.post("/api/work-orders", json={"customer_id": customer["id"], "labor_value": 150}).json()

    r = c.post(f"/api/customers/{customer['id']}/anonymize")
    assert r.status_code == 200
    body = r.json()
    assert body["is_anonymized"] is True
    assert body["anonymized_at"] is not None

    after = c.get(f"/api/customers/{customer['id']}").json()
    assert after["name"] == "Cliente anonimizado"
    assert after["email"] == ""
    assert after["phone"] == ""
    assert after["document"] == ""
    assert after["is_active"] is False
    assert after["is_anonymized"] is True

    # a ordem de serviço em si não foi apagada nem desvinculada
    still_there = c.get(f"/api/work-orders/{wo['id']}")
    assert still_there.status_code == 200


def test_anonymize_is_logged_in_audit_trail():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteLGPD3@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteLGPD3@teste.local", "senha-correta-123")
    customer_id = c.post("/api/customers", json={"name": "Cliente Auditado"}).json()["id"]
    c.post(f"/api/customers/{customer_id}/anonymize")

    logs = c.get("/api/audit-logs", params={"action": "customer.anonymize"}).json()
    assert any(l["entity_id"] == customer_id for l in logs)


def test_lgpd_export_not_found_for_other_company():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteLGPD4@teste.local", "senha-correta-123")
        seed_test_tenant(db, "MANAGER", "gerenteLGPD5@teste.local", "senha-correta-123")
    finally:
        db.close()

    client_a = _login("gerenteLGPD4@teste.local", "senha-correta-123")
    client_b = _login("gerenteLGPD5@teste.local", "senha-correta-123")

    customer_id = client_a.post("/api/customers", json={"name": "Cliente Empresa A"}).json()["id"]
    assert client_b.get(f"/api/customers/{customer_id}/export-data").status_code == 404
