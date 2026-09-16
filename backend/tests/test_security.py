"""
Testes de autenticação/RBAC da FASE 1.

Requer Redis rodando (docker compose up -d redis) porque as sessões vivem
lá — não dá para testar login com sucesso sem um Redis real ou um fake
compatível. O caso "sem cookie" não precisa de Redis (curto-circuita antes).

Não executado neste ambiente de auditoria (sem rede para instalar
fastapi/sqlalchemy/redis, e sem Redis rodando). Rode localmente com:
    docker compose up -d db redis
    cd backend && pip install -r requirements.txt
    pytest tests/test_security.py -v
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_security.db")
os.environ.setdefault("SESSION_COOKIE_SECURE", "false")  # TestClient não usa HTTPS

from fastapi.testclient import TestClient

from app.db.session import Base, SessionLocal, engine
from app.main import app
from tests.conftest import seed_test_tenant as _seed_test_tenant

client = TestClient(app)


def setup_module():
    Base.metadata.create_all(bind=engine)


def test_ai_ask_requires_login():
    # Sem cookie nenhum: curto-circuita em get_current_user antes de tocar Redis.
    r = client.post("/api/ai/ask", json={"question": "oi"})
    assert r.status_code == 401


def test_rag_documents_requires_login():
    r = client.get("/api/rag/documents")
    assert r.status_code == 401


def test_login_wrong_password_is_rejected():
    db = SessionLocal()
    try:
        _seed_test_tenant(db, "MECHANIC", "mecanico1@teste.local", "senha-correta-123")
    finally:
        db.close()

    r = client.post(
        "/api/auth/login",
        json={"email": "mecanico1@teste.local", "password": "senha-errada"},
    )
    assert r.status_code == 401


def test_login_success_then_permitted_action():
    db = SessionLocal()
    try:
        _seed_test_tenant(db, "MANAGER", "gerente1@teste.local", "senha-correta-123")
    finally:
        db.close()

    r = client.post(
        "/api/auth/login",
        json={"email": "gerente1@teste.local", "password": "senha-correta-123"},
    )
    assert r.status_code == 200
    assert "session_id" in r.cookies

    # MANAGER tem "ai.ask" no catálogo — deve conseguir usar o endpoint.
    r2 = client.post(
        "/api/ai/ask",
        json={"question": "qual o status da OS 1?", "use_rag": False, "memory_first": False},
    )
    assert r2.status_code == 200


def test_login_success_but_permission_denied():
    db = SessionLocal()
    try:
        _seed_test_tenant(db, "MECHANIC", "mecanico2@teste.local", "senha-correta-123")
    finally:
        db.close()

    client2 = TestClient(app)  # cookie jar isolado do teste anterior
    r = client2.post(
        "/api/auth/login",
        json={"email": "mecanico2@teste.local", "password": "senha-correta-123"},
    )
    assert r.status_code == 200

    # MECHANIC não tem "rag.ingest" no catálogo — deve receber 403, não 401.
    r2 = client2.post("/api/rag/ingest", files={"file": ("nota.txt", b"conteudo", "text/plain")})
    assert r2.status_code == 403


def test_health_is_public():
    r = client.get("/api/health")
    assert r.status_code == 200
