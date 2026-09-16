"""
Testes do barramento de eventos (FASE 12).

Requer Redis rodando para os testes de integração via API (ver nota em
test_security.py). Não executado neste ambiente de auditoria — rode
localmente com:
    docker compose up -d db redis
    cd backend && pip install -r requirements.txt
    pytest tests/test_events.py -v
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_security.db")
os.environ.setdefault("SESSION_COOKIE_SECURE", "false")

from fastapi.testclient import TestClient

import app.events.handlers as handlers_module
from app.core.events import clear_handlers, publish, subscribe
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


def test_publish_with_no_subscribers_does_nothing():
    # nome de evento exclusivo deste teste — nunca colide com os handlers reais
    publish("test.no_subscribers.unused_event")  # não deve levantar exceção


def test_subscribe_then_publish_calls_handler_with_payload():
    calls = []
    subscribe("test.custom_event", lambda **kw: calls.append(kw))

    publish("test.custom_event", foo="bar", n=42)

    assert calls == [{"foo": "bar", "n": 42}]
    clear_handlers("test.custom_event")


def test_multiple_handlers_all_run_in_order():
    order = []
    subscribe("test.multi_handler_event", lambda **kw: order.append("first"))
    subscribe("test.multi_handler_event", lambda **kw: order.append("second"))

    publish("test.multi_handler_event")

    assert order == ["first", "second"]
    clear_handlers("test.multi_handler_event")


def test_handler_exception_is_isolated_and_does_not_stop_others():
    calls = []

    def boom(**kw):
        raise RuntimeError("handler quebrado de propósito")

    subscribe("test.failing_handler_event", boom)
    subscribe("test.failing_handler_event", lambda **kw: calls.append("segundo handler rodou"))

    publish("test.failing_handler_event")  # não deve levantar exceção

    assert calls == ["segundo handler rodou"]
    clear_handlers("test.failing_handler_event")


def test_closing_work_order_publishes_event_that_triggers_receipt_handler(monkeypatch):
    calls = []
    monkeypatch.setattr(
        handlers_module, "notify_work_order_receipt",
        lambda db, work_order: calls.append(work_order.id),
    )

    db = SessionLocal()
    try:
        seed_test_tenant(db, "MANAGER", "gerenteEVT1@teste.local", "senha-correta-123")
    finally:
        db.close()

    c = _login("gerenteEVT1@teste.local", "senha-correta-123")
    customer_id = c.post("/api/customers", json={"name": "Cliente Evento"}).json()["id"]
    wo = c.post("/api/work-orders", json={"customer_id": customer_id, "labor_value": 80}).json()

    r = c.post(f"/api/work-orders/{wo['id']}/close")
    assert r.status_code == 200
    assert calls == [wo["id"]]  # o handler inscrito em work_order.closed foi chamado


def test_register_handlers_is_idempotent():
    # chamar de novo não deve duplicar a inscrição — se duplicasse, o teste
    # acima veria o handler mockado ser chamado duas vezes para a mesma OS.
    handlers_module.register_handlers()
    handlers_module.register_handlers()

    from app.core.events import _handlers  # acesso direto só para este teste

    assert _handlers["work_order.closed"].count(handlers_module._on_work_order_closed) == 1
