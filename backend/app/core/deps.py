from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.sessions import SessionData, get_session
from app.db.session import get_db


def get_current_user(
    cookie_session_id: str | None = Cookie(default=None, alias=settings.SESSION_COOKIE_NAME),
) -> SessionData:
    """
    Lê o cookie de sessão (nome configurável via SESSION_COOKIE_NAME) e
    resolve os dados da sessão no Redis. 401 se ausente/expirada/inválida.
    """
    data = get_session(cookie_session_id) if cookie_session_id else None
    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão ausente, expirada ou inválida.",
        )
    return data


def require_permission(code: str):
    def dependency(user: SessionData = Depends(get_current_user)) -> SessionData:
        if code not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão '{code}' é necessária para esta ação.",
            )
        return user

    return dependency


def get_tenant_db(user: SessionData = Depends(get_current_user), db: Session = Depends(get_db)) -> Session:
    """
    Sessão de banco já com o contexto de tenant aplicado.

    - Sempre filtra por company_id na camada de aplicação (isso é feito nos
      services, não aqui).
    - Quando o banco é PostgreSQL, também define `app.current_company_id`
      via SET LOCAL, para que as políticas de Row-Level Security (ver
      migration 0002) barrem qualquer query que esqueça o filtro de
      aplicação. Em SQLite (modo dev sem Postgres) essa segunda camada não
      existe — só a filtragem em código vale.
    """
    if db.bind.dialect.name == "postgresql":
        db.execute(text("SET LOCAL app.current_company_id = :cid"), {"cid": user.company_id})
    return db
