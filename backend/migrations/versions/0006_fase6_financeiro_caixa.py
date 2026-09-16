"""fase6_financeiro_caixa

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-13

Cria as tabelas da FASE 6 (Financeiro/Caixa: contas a pagar/receber e
sessões de caixa) e ativa RLS no PostgreSQL, mesmo padrão das migrations
0002 a 0005.

Ordem de criação: finance_entries antes de cash_movements (que a
referencia opcionalmente), cash_sessions antes de cash_movements (que
referencia obrigatoriamente).
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

TABLES = ["finance_entries", "cash_sessions", "cash_movements"]


def upgrade() -> None:
    op.create_table(
        "finance_entries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id", ondelete="SET NULL"), nullable=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("category", sa.String(100), nullable=False, server_default=""),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("paid_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("paid_at", sa.DateTime, nullable=True),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("work_order_id", sa.Integer, sa.ForeignKey("work_orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_finance_entries_company_id", "finance_entries", ["company_id"])
    # Acelera a listagem por status/vencimento (contas em aberto, vencendo hoje, etc.).
    op.create_index("ix_finance_entries_status_due", "finance_entries", ["company_id", "status", "due_date"])

    op.create_table(
        "cash_sessions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(10), nullable=False, server_default="OPEN"),
        sa.Column("opening_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("opened_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("opened_by_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("closing_amount_expected", sa.Numeric(12, 2), nullable=True),
        sa.Column("closing_amount_counted", sa.Numeric(12, 2), nullable=True),
        sa.Column("closed_at", sa.DateTime, nullable=True),
        sa.Column("closed_by_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.String(500), nullable=False, server_default=""),
    )
    op.create_index("ix_cash_sessions_company_id", "cash_sessions", ["company_id"])
    # Acelera a busca pela sessão OPEN atual da empresa/filial.
    op.create_index("ix_cash_sessions_status", "cash_sessions", ["company_id", "branch_id", "status"])

    op.create_table(
        "cash_movements",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cash_session_id", sa.Integer, sa.ForeignKey("cash_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("finance_entry_id", sa.Integer, sa.ForeignKey("finance_entries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("description", sa.String(255), nullable=False, server_default=""),
        sa.Column("created_by_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_cash_movements_company_id", "cash_movements", ["company_id"])
    op.create_index("ix_cash_movements_session_id", "cash_movements", ["cash_session_id"])

    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
            USING (company_id = current_setting('app.current_company_id', true)::int)
            WITH CHECK (company_id = current_setting('app.current_company_id', true)::int)
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for table in TABLES:
            op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
            op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    op.drop_table("cash_movements")
    op.drop_table("cash_sessions")
    op.drop_table("finance_entries")
