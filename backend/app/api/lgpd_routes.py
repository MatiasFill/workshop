from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_db, require_permission
from app.core.sessions import SessionData
from app.schemas.lgpd import AnonymizeResult, CustomerDataExport
from app.services.audit import log_action
from app.services.lgpd import anonymize_customer, export_customer_data

lgpd_router = APIRouter()

# Ambas as rotas exigem `lgpd.manage` (só ADMIN/MANAGER por padrão no
# catálogo) — são operações sensíveis, não o CRUD comum de clientes.


@lgpd_router.get("/customers/{customer_id}/export-data", response_model=CustomerDataExport)
def export_customer_data_route(
    customer_id: int,
    user: SessionData = Depends(require_permission("lgpd.manage")),
    db: Session = Depends(get_tenant_db),
):
    """Direito de acesso/portabilidade (LGPD art. 15/18): todos os dados
    ligados a este cliente — cadastro, veículos, agendamentos, ordens de
    serviço, lançamentos financeiros e notificações."""
    bundle = export_customer_data(db, user.company_id, customer_id)
    if bundle is None:
        raise HTTPException(404, "Cliente não encontrado.")

    log_action(
        db, company_id=user.company_id, user_id=user.user_id, action="customer.export_data",
        entity_type="customer", entity_id=customer_id,
    )
    return bundle


@lgpd_router.post("/customers/{customer_id}/anonymize", response_model=AnonymizeResult)
def anonymize_customer_route(
    customer_id: int,
    user: SessionData = Depends(require_permission("lgpd.manage")),
    db: Session = Depends(get_tenant_db),
):
    """Direito de exclusão/anonimização (LGPD art. 18): sobrescreve os
    campos de identificação pessoal do cliente. Os registros de negócio
    ligados a ele (veículos, OS, financeiro) são preservados — ver
    app/services/lgpd.py para a justificativa legal."""
    customer = anonymize_customer(db, user.company_id, customer_id)
    if customer is None:
        raise HTTPException(404, "Cliente não encontrado.")

    log_action(
        db, company_id=user.company_id, user_id=user.user_id, action="customer.anonymize",
        entity_type="customer", entity_id=customer_id,
    )
    return AnonymizeResult(id=customer.id, is_anonymized=customer.is_anonymized, anonymized_at=customer.anonymized_at)
