"""
Handlers de eventos de domínio (FASE 12). Este módulo só registra
assinaturas no barramento (app/core/events.py) — importar `register_handlers`
e chamá-la uma vez (ver app/main.py) é o que faz os handlers passarem a
reagir aos eventos publicados pelas rotas.

Para adicionar uma nova reação a um evento já publicado em algum lugar:
1. escreva a função handler aqui (ou em outro módulo, se fizer mais sentido);
2. registre com `subscribe("nome.do.evento", minha_funcao)` dentro de
   `register_handlers()`.
Nada mais precisa mudar — a rota que publica o evento não sabe (nem
precisa saber) quantos handlers existem para ele.
"""
from sqlalchemy.orm import Session

from app.core.events import subscribe
from app.models.work_order import WorkOrder
from app.services.notifications import notify_work_order_receipt

_registered = False


def _on_work_order_closed(*, db: Session, work_order: WorkOrder, **_extra) -> None:
    """Reage ao evento `work_order.closed` publicado por
    app/api/work_order_routes.py -> close_work_order: dispara o comprovante
    da OS (e-mail + WhatsApp, com retry automático em caso de falha real —
    ver FASE 11)."""
    notify_work_order_receipt(db, work_order)


def register_handlers() -> None:
    """Idempotente — chamar mais de uma vez (ex.: várias suítes de teste
    importando app.main) não duplica as inscrições."""
    global _registered
    if _registered:
        return
    subscribe("work_order.closed", _on_work_order_closed)
    _registered = True
