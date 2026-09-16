"""
Barramento de eventos síncrono e em processo (FASE 12).

Desacopla "isso aconteceu" (uma rota de negócio publica um evento) de "faça
isso a respeito" (um handler registrado reage a ele) — o item "eventos" do
P3 do roadmap. Mesmo princípio de resiliência já usado em notificações
(FASE 4/5) e auditoria (FASE 8): um handler que falha nunca derruba a ação
de negócio que publicou o evento.

O que isto NÃO é: uma fila real entre processos (isso já existe para
notificações que falham, ver FASE 11 — `NotificationRequest`), nem tem
entrega garantida ou persistência. Handlers rodam de forma síncrona, na
ordem em que foram registrados, dentro da mesma requisição e da mesma
`Session` de banco do publicador. É só uma forma de organizar código:
"fechar uma OS" não precisa mais saber que isso dispara um comprovante —
só publica `work_order.closed` e quem quiser reagir se inscreve.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Callable

logger = logging.getLogger("app.events")

_handlers: dict[str, list[Callable[..., None]]] = defaultdict(list)


def subscribe(event_name: str, handler: Callable[..., None]) -> None:
    """Registra `handler` para rodar toda vez que `event_name` for
    publicado. Chamado a partir de app/events/handlers.py, importado uma
    vez na subida da aplicação (ver app/main.py)."""
    _handlers[event_name].append(handler)


def publish(event_name: str, **payload) -> None:
    """Chama, em ordem, todo handler inscrito em `event_name`. Uma exceção
    em um handler é logada e isolada — nunca propaga para quem publicou o
    evento, e não impede os demais handlers do mesmo evento de rodar."""
    for handler in _handlers.get(event_name, []):
        try:
            handler(**payload)
        except Exception:  # pragma: no cover — isolamento de falha de handler
            logger.exception("Handler %r falhou ao processar o evento %r", handler, event_name)


def clear_handlers(event_name: str | None = None) -> None:
    """Só para uso em testes. Sem argumento, limpa tudo; com `event_name`,
    limpa só aquele evento — use um nome de evento exclusivo do teste para
    não afetar os handlers reais registrados por app/events/handlers.py."""
    if event_name is None:
        _handlers.clear()
    else:
        _handlers.pop(event_name, None)
