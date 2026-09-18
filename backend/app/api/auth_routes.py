from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.passwords import verify_password
from app.core.rate_limit import rate_limit
from app.core.sessions import SessionData, create_session, revoke_session
from app.db.session import get_db
from app.models.rbac import Permission, RolePermission
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, MeResponse
from app.services.audit import log_action

auth_router = APIRouter()


def _load_permissions(db: Session, user: User) -> list[str]:
    role_ids = [ur.role_id for ur in user.roles]
    if not role_ids:
        return []
    rows = (
        db.query(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .filter(RolePermission.role_id.in_(role_ids))
        .distinct()
        .all()
    )
    return [code for (code,) in rows]


@auth_router.post(
    "/auth/login",
    dependencies=[Depends(rate_limit("auth_login", 10, 60))],
)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email, User.is_active.is_(True)))
    # Mensagem de erro genérica de propósito (não revela se o e-mail existe),
    # para dificultar enumeração de contas — o mesmo texto serve para os dois
    # casos (usuário não encontrado / senha errada).
    generic_error = HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos.")
    if not user:
        raise generic_error
    if not verify_password(payload.password, user.password_hash, user.password_salt):
        raise generic_error

    permissions = _load_permissions(db, user)
    token = create_session(
        SessionData(
            user_id=user.id,
            company_id=user.company_id,
            branch_id=user.branch_id,
            name=user.name,
            email=user.email,
            permissions=permissions,
        )
    )
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_TTL_SECONDS,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite="lax",
    )
    log_action(
        db, company_id=user.company_id, user_id=user.id, action="auth.login",
        entity_type="user", entity_id=user.id,
        ip_address=request.client.host if request.client else "",
    )
    return {"status": "ok"}


@auth_router.post("/auth/logout")
def logout(
    request: Request,
    response: Response,
    user: SessionData = Depends(get_current_user),  # garante 401 se já não havia sessão válida
    cookie_session_id: str | None = Cookie(default=None, alias=settings.SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
):
    if cookie_session_id:
        revoke_session(cookie_session_id)
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    log_action(
        db, company_id=user.company_id, user_id=user.user_id, action="auth.logout",
        entity_type="user", entity_id=user.user_id,
        ip_address=request.client.host if request.client else "",
    )
    return {"status": "ok"}


@auth_router.get("/auth/me", response_model=MeResponse)
def me(user: SessionData = Depends(get_current_user)):
    return MeResponse(
        user_id=user.user_id,
        company_id=user.company_id,
        branch_id=user.branch_id,
        name=user.name,
        email=user.email,
        permissions=user.permissions,
    )
