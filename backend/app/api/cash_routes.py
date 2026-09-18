from datetime import datetime
from app.core.clock import utcnow_naive

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_db, require_permission
from app.core.sessions import SessionData
from app.models.finance import CashMovement, CashMovementType, CashSession, CashSessionStatus
from app.schemas.cash import (
    CashMovementCreate,
    CashMovementResponse,
    CashSessionCloseRequest,
    CashSessionOpenRequest,
    CashSessionResponse,
)
from app.services.audit import log_action

cash_router = APIRouter()

# Mesmo princípio das demais rotas: company_id nunca vem do corpo da
# requisição — sempre da sessão autenticada, resolvida por get_tenant_db.


def _session_balance(db: Session, session: CashSession) -> float:
    movements = db.query(CashMovement).filter(CashMovement.cash_session_id == session.id).all()
    balance = float(session.opening_amount)
    for m in movements:
        balance += float(m.amount) if m.type == CashMovementType.IN else -float(m.amount)
    return round(balance, 2)


def _to_response(db: Session, session: CashSession) -> CashSessionResponse:
    expected = float(session.closing_amount_expected) if session.closing_amount_expected is not None else None
    counted = float(session.closing_amount_counted) if session.closing_amount_counted is not None else None
    return CashSessionResponse(
        id=session.id,
        status=session.status,
        opening_amount=float(session.opening_amount),
        opened_at=session.opened_at,
        closing_amount_expected=expected,
        closing_amount_counted=counted,
        cash_difference=round(counted - expected, 2) if expected is not None and counted is not None else None,
        closed_at=session.closed_at,
        notes=session.notes,
        current_balance=_session_balance(db, session),
    )


def _get_session_or_404(db: Session, company_id: int, session_id: int) -> CashSession:
    session = (
        db.query(CashSession)
        .filter(CashSession.id == session_id, CashSession.company_id == company_id)
        .first()
    )
    if not session:
        raise HTTPException(404, "Sessão de caixa não encontrada.")
    return session


@cash_router.get("/cash/sessions", response_model=list[CashSessionResponse])
def list_cash_sessions(
    user: SessionData = Depends(require_permission("cash.manage")),
    db: Session = Depends(get_tenant_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    rows = (
        db.query(CashSession)
        .filter(CashSession.company_id == user.company_id)
        .order_by(CashSession.opened_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [_to_response(db, s) for s in rows]


@cash_router.get("/cash/sessions/current", response_model=CashSessionResponse | None)
def get_current_cash_session(
    user: SessionData = Depends(require_permission("cash.manage")),
    db: Session = Depends(get_tenant_db),
):
    session = (
        db.query(CashSession)
        .filter(CashSession.company_id == user.company_id, CashSession.status == CashSessionStatus.OPEN)
        .first()
    )
    return _to_response(db, session) if session else None


@cash_router.post("/cash/sessions/open", response_model=CashSessionResponse, status_code=201)
def open_cash_session(
    payload: CashSessionOpenRequest,
    user: SessionData = Depends(require_permission("cash.manage")),
    db: Session = Depends(get_tenant_db),
):
    existing = (
        db.query(CashSession)
        .filter(CashSession.company_id == user.company_id, CashSession.status == CashSessionStatus.OPEN)
        .first()
    )
    if existing:
        raise HTTPException(422, f"Já existe uma sessão de caixa aberta (#{existing.id}). Feche-a antes de abrir outra.")

    session = CashSession(
        company_id=user.company_id,
        branch_id=user.branch_id,
        opening_amount=payload.opening_amount,
        opened_by_user_id=user.user_id,
        notes=payload.notes.strip(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    log_action(
        db, company_id=user.company_id, user_id=user.user_id, action="cash_session.open",
        entity_type="cash_session", entity_id=session.id, detail=f"Abertura: R$ {payload.opening_amount:.2f}",
    )
    return _to_response(db, session)


@cash_router.post("/cash/sessions/{session_id}/close", response_model=CashSessionResponse)
def close_cash_session(
    session_id: int,
    payload: CashSessionCloseRequest,
    user: SessionData = Depends(require_permission("cash.manage")),
    db: Session = Depends(get_tenant_db),
):
    session = _get_session_or_404(db, user.company_id, session_id)
    if session.status != CashSessionStatus.OPEN:
        raise HTTPException(422, "Esta sessão de caixa já está fechada.")

    expected = _session_balance(db, session)
    session.closing_amount_expected = expected
    session.closing_amount_counted = payload.closing_amount_counted
    session.status = CashSessionStatus.CLOSED
    session.closed_at = utcnow_naive()
    session.closed_by_user_id = user.user_id
    if payload.notes.strip():
        session.notes = (session.notes + " | " if session.notes else "") + payload.notes.strip()

    db.commit()
    db.refresh(session)
    log_action(
        db, company_id=user.company_id, user_id=user.user_id, action="cash_session.close",
        entity_type="cash_session", entity_id=session.id,
        detail=f"Esperado: R$ {expected:.2f} | Contado: R$ {payload.closing_amount_counted:.2f}",
    )
    return _to_response(db, session)


@cash_router.get("/cash/sessions/{session_id}/movements", response_model=list[CashMovementResponse])
def list_cash_movements(
    session_id: int,
    user: SessionData = Depends(require_permission("cash.manage")),
    db: Session = Depends(get_tenant_db),
):
    _get_session_or_404(db, user.company_id, session_id)
    rows = (
        db.query(CashMovement)
        .filter(CashMovement.cash_session_id == session_id, CashMovement.company_id == user.company_id)
        .order_by(CashMovement.created_at.desc())
        .all()
    )
    return rows


@cash_router.post("/cash/sessions/{session_id}/movements", response_model=CashMovementResponse, status_code=201)
def add_cash_movement(
    session_id: int,
    payload: CashMovementCreate,
    user: SessionData = Depends(require_permission("cash.manage")),
    db: Session = Depends(get_tenant_db),
):
    """Movimento manual (reforço ou sangria) — recebimentos/pagamentos de
    contas devem passar por POST /finance/entries/{id}/pay, que já lança o
    CashMovement correspondente automaticamente."""
    session = _get_session_or_404(db, user.company_id, session_id)
    if session.status != CashSessionStatus.OPEN:
        raise HTTPException(422, "Não é possível lançar movimentos numa sessão de caixa fechada.")

    if payload.type == CashMovementType.OUT and payload.amount > _session_balance(db, session):
        raise HTTPException(422, "Saldo em caixa insuficiente para esta saída.")

    movement = CashMovement(
        company_id=user.company_id,
        cash_session_id=session.id,
        type=payload.type,
        amount=payload.amount,
        description=payload.description.strip(),
        created_by_user_id=user.user_id,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement
