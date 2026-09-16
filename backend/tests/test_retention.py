"""
Testes de retenção de dados (FASE 10).

Requer Redis rodando (ver nota em test_security.py). Não executado neste
ambiente de auditoria — rode localmente com:
    docker compose up -d db redis
    cd backend && pip install -r requirements.txt
    pytest tests/test_retention.py -v
"""
import os
from datetime import datetime, timedelta

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_security.db")
os.environ.setdefault("SESSION_COOKIE_SECURE", "false")

from fastapi.testclient import TestClient

from app.db.session import Base, SessionLocal, engine
from app.main import app
from app.models.customer import Customer
from app.models.notification import NotificationChannel, NotificationLog, NotificationStatus, NotificationType
from tests.conftest import seed_test_tenant

client = TestClient(app)


def setup_module():
    Base.metadata.create_all(bind=engine)


def _login(email: str, password: str) -> TestClient:
    c = TestClient(app)
    r = c.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return c


def test_retention_routes_require_permission():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "RECEPTION", "recepcaoRET@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("recepcaoRET@teste.local", "senha-correta-123")
    assert c.get("/api/retention/candidates").status_code == 403
    assert c.post("/api/retention/purge-notifications").status_code == 403
    assert c.post("/api/retention/anonymize-inactive").status_code == 403


def test_purge_notifications_deletes_only_old_ones():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteRET1@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteRET1@teste.local", "senha-correta-123")

    # cria uma OS e a fecha para gerar notificações (SKIPPED, sem SMTP) recentes
    customer_id = c.post("/api/customers", json={"name": "Cliente Retenção 1"}).json()["id"]
    wo = c.post("/api/work-orders", json={"customer_id": customer_id, "labor_value": 50}).json()
    c.post(f"/api/work-orders/{wo['id']}/close")

    me = c.get("/api/auth/me").json()
    db = SessionLocal()
    try:
        # empurra manualmente uma notificação "antiga" (> janela de retenção) no banco
        old_log = NotificationLog(
            company_id=me["company_id"],
            customer_id=customer_id,
            work_order_id=wo["id"],
            channel=NotificationChannel.EMAIL,
            type=NotificationType.WORK_ORDER_RECEIPT,
            status=NotificationStatus.SKIPPED,
            detail="antiga",
            created_at=datetime.utcnow() - timedelta(days=400),
        )
        db.add(old_log)
        db.commit()
    finally:
        db.close()

    r = c.post("/api/retention/purge-notifications")
    assert r.status_code == 200
    assert r.json()["deleted_count"] == 1  # só o log antigo, não os recentes do fechamento da OS


def test_inactive_customer_without_open_finance_is_a_candidate():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteRET2@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteRET2@teste.local", "senha-correta-123")
    customer_id = c.post("/api/customers", json={"name": "Cliente Inativo"}).json()["id"]

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        customer.created_at = datetime.utcnow() - timedelta(days=365 * 6)  # 6 anos atrás
        db.commit()
    finally:
        db.close()

    candidates = c.get("/api/retention/candidates").json()
    assert any(cand["id"] == customer_id for cand in candidates)


def test_recent_customer_is_not_a_candidate():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteRET3@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteRET3@teste.local", "senha-correta-123")
    customer_id = c.post("/api/customers", json={"name": "Cliente Recente"}).json()["id"]

    candidates = c.get("/api/retention/candidates").json()
    assert not any(cand["id"] == customer_id for cand in candidates)


def test_customer_with_open_finance_entry_is_not_a_candidate():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteRET4@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteRET4@teste.local", "senha-correta-123")
    customer_id = c.post("/api/customers", json={"name": "Cliente Devedor"}).json()["id"]
    c.post("/api/finance/entries", json={"type": "RECEIVABLE", "amount": 100, "due_date": "2026-12-01", "customer_id": customer_id})

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        customer.created_at = datetime.utcnow() - timedelta(days=365 * 6)
        db.commit()
    finally:
        db.close()

    candidates = c.get("/api/retention/candidates").json()
    assert not any(cand["id"] == customer_id for cand in candidates)  # tem pendência financeira


def test_anonymize_inactive_bulk_anonymizes_candidates():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteRET5@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteRET5@teste.local", "senha-correta-123")
    customer_id = c.post("/api/customers", json={"name": "Cliente Bulk Anon"}).json()["id"]

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        customer.created_at = datetime.utcnow() - timedelta(days=365 * 6)
        db.commit()
    finally:
        db.close()

    r = c.post("/api/retention/anonymize-inactive")
    assert r.status_code == 200
    body = r.json()
    assert customer_id in body["customer_ids"]

    after = c.get(f"/api/customers/{customer_id}").json()
    assert after["is_anonymized"] is True

    logs = c.get("/api/audit-logs", params={"action": "customer.anonymize"}).json()
    assert any(l["entity_id"] == customer_id for l in logs)
