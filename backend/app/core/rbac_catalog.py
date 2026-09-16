"""
Catálogo de papéis e permissões da FASE 1.

Isto é a fonte da verdade usada pelo seed (app/db/seed.py) para popular
`roles`, `permissions` e `role_permissions`. Alterações aqui exigem rodar o
seed de novo (ele é idempotente: só cria o que faltar).
"""

ROLES = ["ADMIN", "MANAGER", "RECEPTION", "MECHANIC", "FINANCE", "STOCK_MANAGER"]

PERMISSIONS = [
    "customers.read", "customers.create", "customers.update", "customers.delete",
    "appointments.read", "appointments.create", "appointments.update", "appointments.cancel",
    "work_orders.read", "work_orders.create", "work_orders.update", "work_orders.cancel",
    "stock.read", "stock.create", "stock.adjust",
    "finance.read", "finance.create", "finance.pay", "finance.cancel",
    "cash.manage",
    "suppliers.read", "suppliers.create",
    "purchases.read", "purchases.create", "purchases.update", "purchases.receive", "purchases.cancel",
    "lgpd.manage",
    "users.manage", "settings.manage", "audit.read",
    # Extensões para o módulo de IA/RAG deste scaffold (não previstas no
    # catálogo original da especificação, adicionadas para substituir a
    # medida-ponte da chave de API interna por RBAC real).
    "ai.ask", "ai.memory.manage", "rag.ingest", "rag.read",
    # FASE 4/5: dashboard de relatórios e notificações (comprovante de OS,
    # alerta de revisão próxima do vencimento).
    "reports.read", "notifications.manage",
]

# Mapeamento inicial — pode (e deve) ser ajustado depois via tela de
# administração de papéis; isto é só o ponto de partida razoável da FASE 1.
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "ADMIN": PERMISSIONS,  # admin tem tudo
    "MANAGER": [
        "customers.read", "customers.create", "customers.update",
        "appointments.read", "appointments.create", "appointments.update", "appointments.cancel",
        "work_orders.read", "work_orders.create", "work_orders.update", "work_orders.cancel",
        "stock.read", "stock.create", "stock.adjust",
        "finance.read", "finance.create", "finance.pay", "finance.cancel",
        "cash.manage",
        "suppliers.read", "suppliers.create",
        "purchases.read", "purchases.create", "purchases.update", "purchases.receive", "purchases.cancel",
        "lgpd.manage",
        "audit.read",
        "reports.read", "notifications.manage",
        "ai.ask", "rag.ingest", "rag.read",
    ],
    "RECEPTION": [
        "customers.read", "customers.create", "customers.update",
        "appointments.read", "appointments.create", "appointments.update", "appointments.cancel",
        "work_orders.read", "work_orders.create",
        "ai.ask", "rag.read",
    ],
    "MECHANIC": [
        "appointments.read", "appointments.update",
        "work_orders.read", "work_orders.update",
        "stock.read",
        "ai.ask", "rag.read",
    ],
    "FINANCE": [
        "finance.read", "finance.create", "finance.pay", "finance.cancel",
        "cash.manage",
        "customers.read",
        "suppliers.read",
        "purchases.read",
        "reports.read",
        "ai.ask", "rag.read",
    ],
    "STOCK_MANAGER": [
        "stock.read", "stock.create", "stock.adjust",
        "suppliers.read", "suppliers.create",
        "purchases.read", "purchases.create", "purchases.update", "purchases.receive",
        "finance.read",
        "reports.read",
        "audit.read",
        "ai.ask", "rag.read",
    ],
}
