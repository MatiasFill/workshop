"""
Rate limiting simples em memória, por IP, janela fixa.

Limitação conhecida: só funciona corretamente com 1 processo/worker.
Se o backend rodar com múltiplos workers (uvicorn --workers N) ou
múltiplas réplicas, cada processo terá seu próprio contador e o limite
real será N vezes o configurado. Para produção multi-worker, trocar por
um limiter baseado em Redis (o projeto já tem Redis disponível).
"""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.core.config import settings

_hits: dict[str, deque[float]] = defaultdict(deque)


def _client_key(request: Request, bucket: str) -> str:
    client_ip = request.client.host if request.client else "unknown"
    return f"{bucket}:{client_ip}"


def rate_limit(bucket: str, max_requests: int, window_seconds: int):
    def dependency(request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return
        key = _client_key(request, bucket)
        now = time.monotonic()
        window = _hits[key]
        while window and now - window[0] > window_seconds:
            window.popleft()
        if len(window) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Limite de {max_requests} requisições a cada {window_seconds}s excedido para '{bucket}'.",
            )
        window.append(now)

    return dependency
