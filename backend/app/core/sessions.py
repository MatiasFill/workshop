"""
Sessão de autenticação armazenada no Redis (não em cookie assinado tipo JWT).

Escolha deliberada (ver decisão registrada com o usuário): revogação
instantânea é mais importante aqui do que escalabilidade horizontal sem
estado — e o Redis já é parte da infraestrutura do projeto.

Formato armazenado por chave `session:<token>`: JSON com user_id, company_id,
branch_id e a lista de códigos de permissão (resolvida no login, para evitar
round-trip ao banco em toda requisição). Isso tem um trade-off conhecido:
se as permissões do usuário mudarem, só valem a partir do próximo login —
aceitável para a FASE 1, revisitar se virar problema real.
"""
import json
import secrets
from dataclasses import dataclass, field

from app.core.config import settings
from app.core.redis_client import get_redis

SESSION_PREFIX = "session:"


@dataclass
class SessionData:
    user_id: int
    company_id: int
    branch_id: int | None
    name: str
    email: str
    permissions: list[str] = field(default_factory=list)


def create_session(data: SessionData) -> str:
    token = secrets.token_urlsafe(32)
    r = get_redis()
    r.set(
        f"{SESSION_PREFIX}{token}",
        json.dumps(data.__dict__),
        ex=settings.SESSION_TTL_SECONDS,
    )
    return token


def get_session(token: str) -> SessionData | None:
    if not token:
        return None
    r = get_redis()
    raw = r.get(f"{SESSION_PREFIX}{token}")
    if not raw:
        return None
    payload = json.loads(raw)
    return SessionData(**payload)


def revoke_session(token: str) -> None:
    r = get_redis()
    r.delete(f"{SESSION_PREFIX}{token}")
