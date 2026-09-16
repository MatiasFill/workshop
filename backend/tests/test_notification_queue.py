"""
Testes da fila de notificações com retry/backoff e idempotência (FASE 11).

Requer Redis rodando (ver nota em test_security.py). Não executado neste
ambiente de auditoria — rode localmente com:
    docker compose up -d db redis
    cd backend && pip install -r requirements.txt
    pytest tests/test_notification_queue.py -v
"""
import os
from datetime import datetime, timedelta

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_security.db")
os.environ.setdefault("SESSION_COOKIE_SECURE", "false")

from fastapi.testclient import TestClient

import app.services.notifications as notifications_service
from app.db.session import Base, SessionLocal, engine
from app.main import app
from app.models.notification import NotificationChannel, NotificationStatus, NotificationType
from app.models.notification_queue import NotificationRequest, NotificationRequestStatus
from app.models.user import User
from tests.conftest import seed_test_tenant

client = TestClient(app)


def setup_module():
    Base.metadata.create_all(bind=engine)


def _login(email: str, password: str) -> TestClient:
    c = TestClient(app)
    r = c.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return c


def test_notification_queue_requires_permission():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "RECEPTION", "recepcaoFILA@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("recepcaoFILA@teste.local", "senha-correta-123")
    assert c.get("/api/notifications/queue").status_code == 403
    assert c.post("/api/notifications/process-queue").status_code == 403


def test_enqueue_retry_is_idempotent():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteFILA1@teste.local", "senha-correta-123")
        company_id = db.query(User).filter_by(email="gerenteFILA1@teste.local").first().company_id

        for _ in range(3):
            notifications_service._enqueue_retry(
                db, company_id=company_id, idempotency_key="work_order:999:receipt:email",
                channel=NotificationChannel.EMAIL, type_=NotificationType.WORK_ORDER_RECEIPT,
                customer_id=None, work_order_id=999, subject="Assunto", message="Mensagem",
                last_error="erro simulado",
            )

        count = (
            db.query(NotificationRequest)
            .filter(NotificationRequest.company_id == company_id, NotificationRequest.idempotency_key == "work_order:999:receipt:email")
            .count()
        )
        assert count == 1  # três chamadas, uma linha só
    finally:
        db.close()


def test_failed_send_is_enqueued_for_retry(monkeypatch):
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteFILA2@teste.local", "senha-correta-123")
    finally:
        db.close()

    monkeypatch.setattr(
        notifications_service, "_send_email",
        lambda to, subject, body: (NotificationStatus.FAILED, "erro simulado de SMTP"),
    )

    c = _login("gerenteFILA2@teste.local", "senha-correta-123")
    customer = c.post("/api/customers", json={"name": "Cliente Fila", "email": "cliente@example.com"}).json()
    wo = c.post("/api/work-orders", json={"customer_id": customer["id"], "labor_value": 100}).json()
    c.post(f"/api/work-orders/{wo['id']}/close")

    queue = c.get("/api/notifications/queue").json()
    relevant = [q for q in queue if q["work_order_id"] == wo["id"] and q["channel"] == "EMAIL"]
    assert len(relevant) == 1
    assert relevant[0]["status"] == "PENDING"
    assert relevant[0]["attempts"] == 0


def test_process_queue_retries_and_gives_up_after_max_attempts(monkeypatch):
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteFILA3@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteFILA3@teste.local", "senha-correta-123")
    customer = c.post("/api/customers", json={"name": "Cliente Give Up", "email": "giveup@example.com"}).json()

    me = c.get("/api/auth/me").json()
    db = SessionLocal()
    try:
        req = NotificationRequest(
            company_id=me["company_id"],
            idempotency_key="teste:give-up",
            channel=NotificationChannel.EMAIL,
            type=NotificationType.WORK_ORDER_RECEIPT,
            customer_id=customer["id"],
            work_order_id=None,
            subject="Assunto teste",
            message="Mensagem teste",
            status=NotificationRequestStatus.FAILED,
            attempts=4,
            max_attempts=5,
            next_attempt_at=datetime.utcnow() - timedelta(minutes=1),  # já está no prazo
            last_error="falhas anteriores",
        )
        db.add(req)
        db.commit()
        req_id = req.id
    finally:
        db.close()

    monkeypatch.setattr(
        notifications_service, "_send_email",
        lambda to, subject, body: (NotificationStatus.FAILED, "erro simulado, tentativa final"),
    )

    r = c.post("/api/notifications/process-queue")
    assert r.status_code == 200
    body = r.json()
    assert body["given_up"] == 1  # attempts vira 5, que é o max_attempts

    queue = c.get("/api/notifications/queue").json()
    updated = next(q for q in queue if q["id"] == req_id)
    assert updated["status"] == "GIVEN_UP"
    assert updated["attempts"] == 5


def test_process_queue_marks_sent_on_success(monkeypatch):
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteFILA4@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteFILA4@teste.local", "senha-correta-123")
    customer = c.post("/api/customers", json={"name": "Cliente Sucesso", "email": "sucesso@example.com"}).json()

    me = c.get("/api/auth/me").json()
    db = SessionLocal()
    try:
        req = NotificationRequest(
            company_id=me["company_id"],
            idempotency_key="teste:sucesso",
            channel=NotificationChannel.EMAIL,
            type=NotificationType.WORK_ORDER_RECEIPT,
            customer_id=customer["id"],
            work_order_id=None,
            subject="Assunto teste",
            message="Mensagem teste",
            status=NotificationRequestStatus.PENDING,
            attempts=1,
            max_attempts=5,
            next_attempt_at=datetime.utcnow() - timedelta(minutes=1),
            last_error="uma falha anterior",
        )
        db.add(req)
        db.commit()
        req_id = req.id
    finally:
        db.close()

    monkeypatch.setattr(
        notifications_service, "_send_email",
        lambda to, subject, body: (NotificationStatus.SENT, "Enviado via SMTP."),
    )

    r = c.post("/api/notifications/process-queue")
    assert r.status_code == 200
    assert r.json()["sent"] == 1

    queue = c.get("/api/notifications/queue").json()
    updated = next(q for q in queue if q["id"] == req_id)
    assert updated["status"] == "SENT"
    assert updated["attempts"] == 2
