"""
Testes da Agenda (FASE 3).

Requer Redis rodando (ver nota em test_security.py). Não executado neste
ambiente de auditoria — rode localmente com:
    docker compose up -d db redis
    cd backend && pip install -r requirements.txt
    pytest tests/test_appointments.py -v
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_security.db")
os.environ.setdefault("SESSION_COOKIE_SECURE", "false")

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.db.session import Base, SessionLocal, engine
from app.main import app
from tests.conftest import seed_test_tenant

client = TestClient(app)

BASE_TIME = datetime(2026, 10, 5, 9, 0, 0)


def setup_module():
    Base.metadata.create_all(bind=engine)


def _login(email: str, password: str) -> TestClient:
    c = TestClient(app)
    r = c.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return c


def _create_customer_with_vehicle(c: TestClient, name: str, plate: str) -> tuple[int, int]:
    r = c.post("/api/customers", json={"name": name, "vehicles": [{"plate": plate}]})
    assert r.status_code == 201
    body = r.json()
    return body["id"], body["vehicles"][0]["id"]


def test_appointments_requires_login():
    r = client.get("/api/appointments")
    assert r.status_code == 401


def test_reception_can_schedule_appointment_for_own_customer():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "RECEPTION", "recepcao2@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("recepcao2@teste.local", "senha-correta-123")
    customer_id, vehicle_id = _create_customer_with_vehicle(c, "Cliente Agenda 1", "AGE0001")

    r = c.post(
        "/api/appointments",
        json={
            "customer_id": customer_id,
            "vehicle_id": vehicle_id,
            "scheduled_at": BASE_TIME.isoformat(),
            "duration_minutes": 60,
            "service_type": "Revisão",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "SCHEDULED"
    assert body["customer_name"] == "Cliente Agenda 1"
    assert body["vehicle_plate"] == "AGE0001"


def test_cannot_schedule_vehicle_from_another_customer():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteF@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteF@teste.local", "senha-correta-123")
    customer_1, _ = _create_customer_with_vehicle(c, "Cliente 1", "VEI0001")
    customer_2, vehicle_2 = _create_customer_with_vehicle(c, "Cliente 2", "VEI0002")

    r = c.post(
        "/api/appointments",
        json={"customer_id": customer_1, "vehicle_id": vehicle_2, "scheduled_at": BASE_TIME.isoformat()},
    )
    assert r.status_code == 422


def test_mechanic_double_booking_is_rejected():
    db = SessionLocal()
    try:
        _, admin_user = seed_test_tenant(db, "ADMIN", "adminG@teste.local", "senha-correta-123")
        mechanic_id = admin_user.id  # reaproveita o próprio usuário como "mecânico" só para o teste
    finally:
        db.close()

    c = _login("adminG@teste.local", "senha-correta-123")
    customer_id, _ = _create_customer_with_vehicle(c, "Cliente Conflito", "CFL0001")

    r1 = c.post(
        "/api/appointments",
        json={
            "customer_id": customer_id,
            "mechanic_id": mechanic_id,
            "scheduled_at": BASE_TIME.isoformat(),
            "duration_minutes": 90,
        },
    )
    assert r1.status_code == 201

    # Novo agendamento começa 30min depois do primeiro (que dura 90min) —
    # sobrepõe, deve ser rejeitado.
    overlapping_start = BASE_TIME + timedelta(minutes=30)
    r2 = c.post(
        "/api/appointments",
        json={
            "customer_id": customer_id,
            "mechanic_id": mechanic_id,
            "scheduled_at": overlapping_start.isoformat(),
            "duration_minutes": 60,
        },
    )
    assert r2.status_code == 409

    # Já um horário depois do fim do primeiro (9:00 + 90min = 10:30) não conflita.
    non_overlapping_start = BASE_TIME + timedelta(minutes=90)
    r3 = c.post(
        "/api/appointments",
        json={
            "customer_id": customer_id,
            "mechanic_id": mechanic_id,
            "scheduled_at": non_overlapping_start.isoformat(),
            "duration_minutes": 60,
        },
    )
    assert r3.status_code == 201


def test_cancelled_appointment_frees_up_the_slot():
    db = SessionLocal()
    try:
        _, admin_user = seed_test_tenant(db, "ADMIN", "adminH@teste.local", "senha-correta-123")
        mechanic_id = admin_user.id
    finally:
        db.close()

    c = _login("adminH@teste.local", "senha-correta-123")
    customer_id, _ = _create_customer_with_vehicle(c, "Cliente Cancelamento", "CNL0001")

    r1 = c.post(
        "/api/appointments",
        json={"customer_id": customer_id, "mechanic_id": mechanic_id, "scheduled_at": BASE_TIME.isoformat()},
    )
    appt_id = r1.json()["id"]

    r2 = c.post(f"/api/appointments/{appt_id}/cancel")
    assert r2.status_code == 200
    assert r2.json()["status"] == "CANCELLED"

    # Mesmo horário, agora livre porque o anterior foi cancelado.
    r3 = c.post(
        "/api/appointments",
        json={"customer_id": customer_id, "mechanic_id": mechanic_id, "scheduled_at": BASE_TIME.isoformat()},
    )
    assert r3.status_code == 201


def test_mechanic_role_cannot_create_appointment():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MECHANIC", "mecanico4@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("mecanico4@teste.local", "senha-correta-123")
    r = c.post("/api/appointments", json={"customer_id": 1, "scheduled_at": BASE_TIME.isoformat()})
    assert r.status_code == 403


def test_appointments_are_isolated_by_company():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteI@teste.local", "senha-correta-123")
        seed_test_tenant(db, "MANAGER", "gerenteJ@teste.local", "senha-correta-123")
    finally:
        db.close()

    client_a = _login("gerenteI@teste.local", "senha-correta-123")
    client_b = _login("gerenteJ@teste.local", "senha-correta-123")

    customer_id, _ = _create_customer_with_vehicle(client_a, "Cliente Empresa A", "ISO0001")
    r = client_a.post(
        "/api/appointments", json={"customer_id": customer_id, "scheduled_at": BASE_TIME.isoformat()}
    )
    appt_id = r.json()["id"]

    r2 = client_b.get(f"/api/appointments/{appt_id}")
    assert r2.status_code == 404
