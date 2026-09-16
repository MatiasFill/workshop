from pydantic import BaseModel, Field


class MonthlyPoint(BaseModel):
    month: str  # "2026-08"
    revenue: float
    profit: float
    work_orders_closed: int


class DashboardReport(BaseModel):
    # Estoque
    stock_value: float  # soma de quantity * cost_price de itens ativos
    stock_critical_items: int  # itens com quantity <= min_quantity

    # Ordens de serviço
    open_work_orders: int

    # Clientes
    customers_total: int
    customers_new_this_month: int

    # Financeiro (mês atual vs. mês anterior)
    revenue_this_month: float
    profit_this_month: float
    revenue_last_month: float
    profit_last_month: float

    # FASE 6 — contas a pagar/receber em aberto (inclui vencidas) e saldo do
    # caixa aberto no momento (null se não houver sessão de caixa aberta).
    receivables_pending: float
    payables_pending: float
    cash_balance: float | None = None

    # Série para o gráfico de comparação mês a mês (últimos meses, mais recente por último)
    monthly_series: list[MonthlyPoint] = Field(default_factory=list)
