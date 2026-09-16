"""
Testes de Financeiro e Caixa (FASE 6).

Requer Redis rodando (ver nota em test_security.py). Não executado neste
ambiente de auditoria — rode localmente com:
    docker compose up -d db redis
    cd backend && pip install -r requirements.txt
    pytest tests/test_finance.py -v
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


def test_finance_requires_login():
    r = client.get("/api/finance/entries")
    assert r.status_code == 401


def test_create_and_pay_receivable_in_full():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "FINANCE", "financeiro1@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("financeiro1@teste.local", "senha-correta-123")

    r = c.post(
        "/api/finance/entries",
        json={"type": "RECEIVABLE", "category": "Venda avulsa", "amount": 300, "due_date": "2026-09-20"},
    )
    assert r.status_code == 201
    entry = r.json()
    assert entry["status"] == "PENDING"
    assert entry["remaining_amount"] == 300

    r2 = c.post(f"/api/finance/entries/{entry['id']}/pay", json={})
    assert r2.status_code == 200
    paid = r2.json()
    assert paid["status"] == "PAID"
    assert paid["remaining_amount"] == 0
    assert paid["paid_amount"] == 300


def test_partial_payment_keeps_entry_pending():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "FINANCE", "financeiro2@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("financeiro2@teste.local", "senha-correta-123")
    r = c.post("/api/finance/entries", json={"type": "PAYABLE", "category": "Fornecedor", "amount": 500, "due_date": "2026-09-20"})
    entry_id = r.json()["id"]

    r2 = c.post(f"/api/finance/entries/{entry_id}/pay", json={"amount": 200})
    assert r2.status_code == 200
    body = r2.json()
    assert body["status"] == "PENDING"
    assert body["paid_amount"] == 200
    assert body["remaining_amount"] == 300


def test_cannot_pay_more_than_remaining():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "FINANCE", "financeiro3@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("financeiro3@teste.local", "senha-correta-123")
    r = c.post("/api/finance/entries", json={"type": "PAYABLE", "amount": 100, "due_date": "2026-09-20"})
    entry_id = r.json()["id"]

    r2 = c.post(f"/api/finance/entries/{entry_id}/pay", json={"amount": 150})
    assert r2.status_code == 422


def test_overdue_entry_computed_on_read():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "FINANCE", "financeiro4@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("financeiro4@teste.local", "senha-correta-123")
    r = c.post("/api/finance/entries", json={"type": "RECEIVABLE", "amount": 50, "due_date": "2020-01-01"})
    entry_id = r.json()["id"]

    r2 = c.get(f"/api/finance/entries/{entry_id}")
    assert r2.json()["status"] == "OVERDUE"


def test_reception_cannot_access_finance():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "RECEPTION", "recepcaoFIN@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("recepcaoFIN@teste.local", "senha-correta-123")
    assert c.get("/api/finance/entries").status_code == 403
    assert c.get("/api/cash/sessions").status_code == 403


def test_cash_session_open_close_and_movements():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "FINANCE", "caixa1@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("caixa1@teste.local", "senha-correta-123")

    r = c.post("/api/cash/sessions/open", json={"opening_amount": 100})
    assert r.status_code == 201
    session = r.json()
    assert session["status"] == "OPEN"
    assert session["current_balance"] == 100

    # não pode abrir uma segunda sessão enquanto a primeira estiver aberta
    r_dup = c.post("/api/cash/sessions/open", json={"opening_amount": 50})
    assert r_dup.status_code == 422

    r2 = c.post(f"/api/cash/sessions/{session['id']}/movements", json={"type": "IN", "amount": 250, "description": "Recebimento avulso"})
    assert r2.status_code == 201

    r3 = c.post(f"/api/cash/sessions/{session['id']}/movements", json={"type": "OUT", "amount": 900, "description": "Saída inválida"})
    assert r3.status_code == 422  # saldo insuficiente (100 + 250 = 350 disponível)

    current = c.get("/api/cash/sessions/current").json()
    assert current["current_balance"] == 350

    r4 = c.post(f"/api/cash/sessions/{session['id']}/close", json={"closing_amount_counted": 340})
    assert r4.status_code == 200
    closed = r4.json()
    assert closed["status"] == "CLOSED"
    assert closed["closing_amount_expected"] == 350
    assert closed["cash_difference"] == -10  # quebra de caixa de R$ 10


def test_paying_entry_registers_cash_movement_when_session_open():
    db = SessionLocal()
    try:
        seed_test_tenant(db, "FINANCE", "caixa2@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("caixa2@teste.local", "senha-correta-123")
    session = c.post("/api/cash/sessions/open", json={"opening_amount": 0}).json()

    entry = c.post("/api/finance/entries", json={"type": "RECEIVABLE", "amount": 120, "due_date": "2026-09-20"}).json()
    c.post(f"/api/finance/entries/{entry['id']}/pay", json={})

    current = c.get("/api/cash/sessions/current").json()
    assert current["current_balance"] == 120

    movements = c.get(f"/api/cash/sessions/{session['id']}/movements").json()
    assert any(m["finance_entry_id"] == entry["id"] for m in movements)
